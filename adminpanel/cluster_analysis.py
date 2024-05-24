from string import punctuation
import numpy as np
import pandas as pd
import pymorphy2
from rake_nltk import Rake
from scipy.cluster.hierarchy import linkage, fcluster
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from config import app


class ClusterAnalysis:
    """Модуль кластерного анализа"""

    def __init__(self) -> None:
        self.nlp = spacy.load("ru_core_news_sm")
        self.morph = pymorphy2.MorphAnalyzer()
        self.spec_words = app.config["ABBREVIATION_UTMN"]

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
            true_words_string = ""

            words = words.translate({ord(c): "" for c in punctuation})
            for word in words.split(" "):
                # проверяем слово, на абривиатуру ТюмГУ
                if word.lower() in self.spec_words:
                    score = 1
                else:
                    score = self.morph.parse(word)[0].score
                # добовляем слово в новую строку
                if score >= threshold:
                    true_words_string += " " + word
            # возвращаем слово или False
            if true_words_string == "":
                return None
            x1 = len(words.split(" ")) / 2
            x2 = len(true_words_string.split(" ")) - 1
            if x1 < x2:
                return words
            return None

        df["text"] = df["text"].apply(del_spec_sim)
        df["text"] = df["text"].apply(found_trash_words)
        df = df.dropna()
        return df

    def vectorization(self, df: pd.DataFrame) -> np.ndarray:
        """Метод векторизации предложений, подлежащих анализу

        Args:
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            np.ndarray: массив, содержащий в каждой строке векторные представления вопросов
        """

        vectorizer = TfidfVectorizer(min_df=2)
        scaler = StandardScaler()
        lower_stopword_lemmatize = lambda text: " ".join(
            [
                token.lemma_
                for token in self.nlp(str(text))
                if not token.is_stop and token.pos_ != "PUNCT"
            ]
        )
        df["text_lemma"] = df["text"].apply(lower_stopword_lemmatize)
        vectors = vectorizer.fit_transform(df["text_lemma"])
        vectors = scaler.fit_transform(vectors.toarray())
        return vectors

    def clustersing(
        self, vectors: np.ndarray, df: pd.DataFrame
    ) -> dict[int, list[tuple[str, str]]]:
        """Модуль кластеризации предложений

        Args:
            vectors (np.ndarray): массив, содержащий в каждой строке векторные представления вопросов
            df (pd.DataFrame): датафрейм содержания и даты появления вопроса

        Returns:
            dict[int, list[tuple[str, str]]]: словарь, содержащий предложения с датами по кластерам
        """

        for i in range(len(vectors)):
            if vectors[i].sum() == 0:
                vectors[i][0] = 10 ** (-20)
        clusters_hier = linkage(vectors, method="complete", metric="cosine")
        clusters_hier = fcluster(clusters_hier, 0.9, criterion="distance")

        clusters = dict()
        df = df.reset_index(drop=True)
        for i in range(len(clusters_hier)):
            if clusters_hier[i] in clusters.keys():
                clusters[clusters_hier[i]].append(
                    (df["text"].iloc[i], df["date"].iloc[i])
                )
            else:
                clusters[clusters_hier[i]] = [(df["text"].iloc[i], df["date"].iloc[i])]
        arr = []
        for i in clusters.keys():
            if len(clusters[i]) < 3:
                arr.append(i)
        for i in arr:
            clusters.pop(i)
        return clusters

    def keywords_extracting(self, sentences: list[str]) -> list[str]:
        """Модуль формирования ключевых слов по списку предложений

        Args:
            sentences (list[str]): список предолжений, по которым нужно составить ключевые слова

        Returns:
            list[str]: ключевые слова и выражения
        """

        rake = Rake(
            min_length=2,
            punctuations={i for i in punctuation},
            language="russian",
            include_repeated_phrases=False,
        )
        rake.extract_keywords_from_text(". ".join(sentences))
        return rake.get_ranked_phrases()[:10]

    def get_clusters_keywords(
        self, questions: list[dict[str, str]]
    ) -> list[tuple[list[str] | str]]:
        """Логика кластеризации текстовых данных

        Args:
            questions (list[dict[str, str]]): список вопросов, подлежащих анализу

        Returns:
            list[tuple[list[str] | str]]: список кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        # TODO: refactor
        if len(questions) < 2:
            return []

        try:
            df = pd.DataFrame(questions)
            df = self.preprocessing(df)
            vectors = self.vectorization(df)
            clusters = self.clustersing(vectors, df)

            data = []
            for cluster in clusters.values():
                sentences = []
                date = "2024-01-01"
                for sentence in cluster:
                    sentences.append(sentence[0])
                    if date < sentence[1]:
                        date = sentence[1]
                data.append((sentences, self.keywords_extracting(sentences), date))
            data = sorted(data, key=lambda dt: len(dt[0]), reverse=True)
            return data
        except:
            return []


def Fprint(arr):
    for a in arr:
        for i in a[0]:
            print(i)
        print("=" * 20)
        print(a[1])
        print(a[2])
        print()


if __name__ == "__main__":
    arr = []
    with open("database.csv", "r", encoding="utf-8") as f:
        s = f.readline()
        while s:
            arr.append({"text": s.split(" --- ")[0], "date": s.split(" --- ")[1][:-1]})
            s = f.readline()

    CA = ClusterAnalysis()
    data = CA.get_clusters_keywords(arr)
    Fprint(data)
