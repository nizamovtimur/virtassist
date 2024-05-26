from enum import Enum
from string import punctuation
import numpy as np
import pandas as pd
import pymorphy2
from rake_nltk import Rake
from scipy.cluster.hierarchy import linkage, fcluster
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from config import app


class mark_of_question(Enum):
    have_not_answer = 0
    have_low_score = 1
    have_high_score = 2
    have_not_score = 3


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
    ) -> dict[int, list[tuple[str, str, mark_of_question]]]:
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
        range_of_values = np.arange(0.01, clusters_hier[:, 2].max(), 0.01)
        max_sil = 0
        threshold_value = 0.59
        for i in range_of_values:
            clusters = fcluster(clusters_hier, i, criterion="distance")
            sil = silhouette_score(vectors, clusters, metric="cosine")
            if sil > max_sil:
                max_sil = sil
                threshold_value = i
        clusters_hier = fcluster(clusters_hier, threshold_value, criterion="distance")

        clusters = dict()
        df = df.reset_index(drop=True)
        for i in range(len(clusters_hier)):
            if clusters_hier[i] in clusters.keys():
                clusters[clusters_hier[i]].append(
                    (df["text"].iloc[i], df["date"].iloc[i], df["type"].iloc[i])
                )
            else:
                clusters[clusters_hier[i]] = [
                    (df["text"].iloc[i], df["date"].iloc[i], df["type"].iloc[i])
                ]
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
        self, questions: list[dict[str, str | mark_of_question]]
    ) -> list[tuple[list[str] | str | mark_of_question]]:  # TODO: refactor
        """Логика кластеризации текстовых данных

        Args:
            questions (list[dict[str, str]]): список вопросов, подлежащих анализу

        Returns:
            list[tuple[list[str] | str | mark_of_question]]: список кортежей, для каждого: список вопросов, список ключевых слов, временной промежуток вопросов по кластеру, метка вопроса
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
                types = []
                date_max = "2024-01-01"
                date_min = "9999-12-12"
                for sentence in cluster:
                    sentences.append(sentence[0])  # TODO: добавить предложениям Enum
                    types.append(
                        sentence[2]
                    )  # TODO: Добавить в sentences (Временный костыль, чтобы у Андрея пока что ничего не сломалось)
                    if date_max < sentence[1]:
                        date_max = sentence[1]
                    if date_min > sentence[1]:
                        date_min = sentence[1]
                data.append(
                    (
                        sentences,
                        self.keywords_extracting(sentences),
                        "с " + date_min + " по " + date_max,
                        types,  # TODO: Добавить в sentences
                    )
                )
            data = sorted(data, key=lambda dt: len(dt[0]), reverse=True)
            return data
        except:
            return []


def Fprint(arr):
    for a in arr:
        for i in range(len(a[0])):
            print(a[0][i], "\t", a[3][i].name)
        print("=" * 20)
        print(a[1])
        print(a[2])
        print()


if __name__ == "__main__":
    arr = []
    with open("database.csv", "r", encoding="utf-8") as f:
        s = f.readline()
        while s:
            x = int(s.split(" --- ")[2])
            if x == 0:
                x = mark_of_question.have_not_answer
            elif x == 1:
                x = mark_of_question.have_low_score
            elif x == 2:
                x = mark_of_question.have_high_score
            else:
                x = mark_of_question.have_not_score
            arr.append(
                {"text": s.split(" --- ")[0], "date": s.split(" --- ")[1], "type": x}
            )
            s = f.readline()

    CA = ClusterAnalysis()
    data = CA.get_clusters_keywords(arr)
    Fprint(data)
