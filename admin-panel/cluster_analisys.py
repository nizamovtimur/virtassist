from string import punctuation
from typing import Union

import nltk
import numpy as np
import pandas as pd
import pymorphy2
from rake_nltk import Rake
from scipy.cluster.hierarchy import linkage, fcluster
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class ClusterAnalisys:
    """Модуль кластерного анализа"""

    def __init__(self) -> None:
        nltk.download("stopwords")
        nltk.download("punkt")
        self.nlp = spacy.load("ru_core_news_sm")
        self.morph = pymorphy2.MorphAnalyzer()

    def preprocessing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Метод предобработки данных

        Args:
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            pd.DataFrame: тот же датафрейм, но без спецсимволов и мусорных вопросов
        """

        def del_spec_sim(s: str) -> str:
            """Метод удаления специальных символов и двойных пробелов

            Args:
                s (str): пердложение, которое нужно предобработать

            Returns:
                str: то же предложение, но без спец. символов и двойных пробелов
            """

            s = s.replace("\\n", " ").replace("\\t", " ").replace("  ", " ")
            while "  " in s:
                s = s.replace("  ", " ")
            return s

        # def found_trash_words(words: str) -> str | None:
        def found_trash_words(words: str) -> str | None:
            """Метод, который помечает на удаление предложения, которые по большей части состоят из бессмысленных наборов букв

            Args:
                words (str): предложение, которое нужно предобработать

            Returns:
                str | None: то же предложение, если по большей части состоит из осмысленных слов, иначе None
            """

            if words == "":
                return None
            threshold = 0.6  # нижняя граница для того, чтобы считать набор букв словом
            s = ""

            spec_words = [
                "тюмгу",
                "шкн",
                "игип",
                "фэи",
                "соцгум",
                "ипип",
                "биофак",
                "инзем",
                "инхим",
                "фти",
                "инбио",
                "ифк",
                "ед",
                "шпи",
            ]  # временный костыль для нахождения абривиатур ТюмГУ
            z = {i for i in punctuation}  # набор пунктуации
            for word in words.split(" "):
                # берём по слову, не нарушая пунктуации
                x = word[-1]
                if x in z:
                    word = word[:-1]
                else:
                    x = ""
                # проверяем слово, на абривиатуру ТюмГУ
                if word.lower() in spec_words:
                    score = 1
                else:
                    p = self.morph.parse(word)
                    score = p[0].score
                # добовляем слово в новую строку
                if score >= threshold:
                    s += " " + word + x
            # возвращаем слово или False
            if s == "":
                return None
            x1 = len(words.split(" ")) / 2
            x2 = len(s.split(" ")) - 1
            if x1 < x2:
                return words
            return None

        df["text"] = df["text"].apply(del_spec_sim)
        df["text"] = df["text"].apply(found_trash_words)
        df = df.dropna()
        return df

    def vectorizing(self, df: pd.DataFrame) -> np.ndarray:
        """Метод векторизации предложений, подлежащих анализу

        Args:
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            np.ndarray: массив, содержащий в каждой строке векторные представления вопросов
        """

        vectorizer = TfidfVectorizer(min_df=2)
        scaler = StandardScaler()

        def lower_stopword_lemmatize(text: str) -> str:
            """Возвращает леммы по предложениям

            Args:
                text (str): исходное предложение

            Returns:
                str: итоговые леммы
            """

            doc = self.nlp(str(text))
            return " ".join(
                [
                    token.lemma_
                    for token in doc
                    if not token.is_stop and token.pos_ != "PUNCT"
                ]
            )

        df["text_lemma"] = df["text"].apply(lower_stopword_lemmatize)

        X = vectorizer.fit_transform(df["text_lemma"])
        vectorizer.get_feature_names_out()

        vectors = pd.DataFrame(
            X.toarray().transpose(), vectorizer.get_feature_names_out()
        )
        scaler.fit(vectors)
        vectors = scaler.transform(vectors).transpose()
        return vectors

    def clustersing(self, vectors: np.ndarray, df: pd.DataFrame) -> dict:
        """Модуль кластеризации предложений

        Args:
            vectors (np.ndarray): массив, содержащий в каждой строке векторные представления вопросов
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            dict: словарь, содержащий предложения по кластерам
        """

        samples = vectors
        for i in range(len(samples)):
            if samples[i].sum() == 0:
                samples[i][0] = 10 ** (-20)
        clusters_hier = linkage(samples, method="complete", metric="cosine")
        clusters_hier = fcluster(clusters_hier, 0.9, criterion="distance")

        clusters = dict()
        df["index"] = [i for i in range(len(df))]
        for i in range(len(clusters_hier)):
            inf = df.loc[df["index"] == i, ["text", "date"]].iloc[0]
            if clusters_hier[i] in clusters.keys():
                clusters[clusters_hier[i]].append([inf["text"], inf["date"]])
            else:
                clusters[clusters_hier[i]] = [[inf["text"], inf["date"]]]
        arr = []
        for i in clusters.keys():
            if len(clusters[i]) < 3:
                arr.append(i)
        for i in arr:
            clusters.pop(i)
        return clusters

    def keywords_extracting(self, arr: list[str]) -> list[str]:
        """Модуль формирования ключевых слов по списку предложений

        Args:
            arr (list[str]): список предолжений, по которым нужно составить ключевые слова

        Returns:
            list[str]: ключевые слова и выражения
        """

        rake = Rake(
            min_length=2, punctuations={i for i in punctuation}, language="russian"
        )
        s = ""
        for i in arr:
            s += ". " + i
        rake.extract_keywords_from_text(s)
        return rake.get_ranked_phrases()[:10]

    def get_clusters_keywords(
        self, questions: list[dict[str, str]]
    ) -> list[tuple[list[str] | str]]:
        """Логика кластеризации текстовых данных

        Args:
            questions (list[dict[str, str]]): список вопросов, подлежащих анализу

        Returns:
            list[tuple[list[str] | str]]: писок кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        df = pd.DataFrame(questions)
        df = self.preprocessing(df)
        vectors = self.vectorizing(df)
        clusters = self.clustersing(vectors, df)

        data = []
        for i in clusters.keys():
            conv = []
            date = "2024-01-01"
            for j in clusters[i]:
                conv.append(j[0])
                if date < j[1]:
                    date = j[1]
            data.append((conv, self.keywords_extracting(conv), date))
        data = sorted(data, key=lambda dt: len(dt[0]), reverse=True)
        return data


def Fprint(arr):
    for a in arr:
        for i in a[0]:
            print(i)
        print("=" * 20)
        print(a[1])
        print(a[2])
        print()


def main():
    arr = []
    with open("database.csv", "r", encoding="utf-8") as f:
        s = f.readline()
        while s:
            arr.append({"text": s.split(" --- ")[0], "date": s.split(" --- ")[1][:-1]})
            s = f.readline()

    CA = ClusterAnalisys()
    data = CA.get_clusters_keywords(arr)
    Fprint(data)


if __name__ == "__main__":
    main()
