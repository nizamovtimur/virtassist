import pandas as pd
import numpy as np
import pymorphy2
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.cluster import AgglomerativeClustering
from string import punctuation
import nltk
from rake_nltk import Rake


class ClusterAnalisys:
    """Модуль кластерного анализа"""

    def __init__(self) -> None:
        nltk.download("stopwords")
        nltk.download("punkt")
        self.nlp = spacy.load("ru_core_news_sm")
        self.morph = pymorphy2.MorphAnalyzer()
        self.vectorizer = TfidfVectorizer(min_df=2)
        self.scaler = StandardScaler()
        self.rake = Rake(
            min_length=2, punctuations={i for i in punctuation}, language="russian"
        )

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
        def found_trash_words(words: str):  # type: ignore
            """Метод, который помечает на удаление предложения, которые по большей части состоят из бессмысленных наборов букв

            Args:
                words (str): предложение, которое нужно предобработать

            Returns:
                str | None: то же предложение, если по большей части состоит из осмысленных слов, иначе None
            """

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
                    score = p[0].score  # type: ignore
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

    def vectorize(self, df: pd.DataFrame) -> np.ndarray:
        """Метод векторизации предложений, подлежащих анализу

        Args:
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            np.ndarray: датафрейм, содержащий в каждой строке векторные представления вопросов
        """

        df1 = pd.DataFrame(columns=["pred"])
        for i in range(len(df)):
            doc = self.nlp(str(df["text"].iloc[i]))
            df1.loc[i] = [
                " ".join(
                    [
                        token.lemma_
                        for token in doc
                        if not token.is_stop and token.pos_ != "PUNCT"
                    ]
                )
            ]

        X = self.vectorizer.fit_transform(df1["pred"])
        self.vectorizer.get_feature_names_out()

        vectors = pd.DataFrame(
            X.toarray().transpose(), self.vectorizer.get_feature_names_out()  # type: ignore
        )
        self.scaler.fit(vectors)
        vectors = self.scaler.transform(vectors).transpose()  # type: ignore
        return vectors

    def clustersing(self, vectors: np.ndarray, df: pd.DataFrame) -> dict:
        """Модуль кластеризации предложений

        Args:
            vectors (np.ndarray): датафрейм, содержащий в каждой строке векторные представления вопросов
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

    def get_keywords(self, arr: list[str]) -> list[str]:
        """Модуль формирования ключевых слов по списку предложений

        Args:
            arr (list[str]): список предолжений, по которым нужно составить ключевые слова

        Returns:
            list[str]: ключевые слова и выражения
        """

        s = ""
        for i in arr:
            s += ". " + i
        result = []
        self.rake.extract_keywords_from_text(s)
        return self.rake.get_ranked_phrases()[:10]

    # def get_data(self, clusters: dict) -> list[tuple[list[str] | str]]:
    def get_data(self, clusters: dict):
        """Форматирование кластеров для визуализации

        Args:
            clusters (dict): словарь, содержащий предложения по кластерам

        Returns:
            list[tuple[list[str] | str]]: список кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        data = []
        for i in clusters.keys():
            conv = []
            date = "2024-01-01"
            for j in clusters[i]:
                conv.append(j[0])
                if date < j[1]:
                    date = j[1]
            data.append((conv, self.get_keywords(conv), date))
        data = sorted(data, key=lambda dt: len(dt[0]), reverse=True)
        return data

    # def get_clusters_keywords(self, questions: list[dict[str, str]]) -> list[tuple[list[str] | str]]:
    def get_clusters_keywords(self, questions: list[dict[str, str]]):
        """Логика кластеризации текстовых данных

        Args:
            questions (list[dict[str, str]]): список вопросов, подлежащих анализу

        Returns:
            list[tuple[list[str] | str]]: писок кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        df = pd.DataFrame(questions)
        df = self.preprocessing(df)
        vectors = self.vectorize(df)
        clusters = self.clustersing(vectors, df)
        return self.get_data(clusters)
