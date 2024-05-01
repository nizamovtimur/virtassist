import pandas as pd
import pymorphy2
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, fcluster
from string import punctuation
import nltk
from rake_nltk import Rake


class ClusterAnalisys:
    """Модуль кластерного анализа

    Args:
        self.vectors (pandas.core.frame.DataFrame | None): векторные предстовления текстовых данных
        self.clusters (dict[list[list]] | None): вся информация о кластерах (предложения, даты)
        self.nlp (spacy.lang.ru.Russian): модель для nlp
        self.morph (pymorphy2.analyzer.MorphAnalyzer): модуль для оценки слова на осмысленность
        self.vectorizer (sklearn.feature_extraction.text.TfidfVectorizer): модуль TF-IDF векторизации предложений
        self.scaler (sklearn.preprocessing._data.StandardScaler): модуль стандартизации
        self.rake (): модуль выделения ключевых слов
    """

    def __init__(self) -> None:
        nltk.download("stopwords")
        nltk.download("punkt")
        # self.punct = [i for i in punctuation]
        self.nlp = spacy.load("ru_core_news_sm")
        self.morph = pymorphy2.MorphAnalyzer()
        self.vectorizer = TfidfVectorizer(min_df=2)
        self.scaler = StandardScaler()
        self.rake = Rake(min_length=2, punctuations=punctuation, language="russian")

    def init_dataset(self, questions):
        """Перевод списка QuestionAnswer`ов в DataFrame

        Args:
            questions (list[QuestionAnswer]): список вопросов, подлежащих анализу
        """

        self.df = pd.DataFrame(questions)

    def preprocessing(self):
        """Модуль предобработки данных"""

        def del_spec_sim(s):
            """Модуль удаления специальных символов и двойных пробелов

            Args:
                s (str): пердложение, которое нужно предобработать
            """

            s = s.replace("\\n", " ").replace("\\t", " ").replace("  ", " ")
            while "  " in s:
                s = s.replace("  ", " ")
            return s

        def found_unrus_conves(s):
            """Модуль, который помечает на удаление предложения, не содержащие русских букв

            Args:
                s (str): пердложение, которое нужно предобработать
            """

            rus_alph = "йцукенгшщзхъфывапролджэячсмитьбюё"
            for s1 in s:
                if s1 in rus_alph:
                    return s
            return False

        def found_trash_words(words):
            """Модуль, который помечает на удаление предложения, которые по большей части состоят из бессмысленных наборов букв

            Args:
                words (str): пердложение, которое нужно предобработать
            """

            threshold = 0.6  # нижняя граница для того, чтобы считать набор букв словом
            s = ""

            SpecWords = [
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
            z = (".", ",", "!", "?")  # набор пунктуации
            for word in words.split(" "):
                # берём по слову, не нарушая пунктуации
                if len(word) < 2:
                    if word == " ":
                        print(">>>")
                x = word[-1]
                if x in z:
                    word = word[:-1]
                else:
                    x = ""
                # проверяем слово, на абривиатуру ТюмГУ
                if word.lower() in SpecWords:
                    score = 1
                else:
                    p = self.morph.parse(word)
                    score = p[0].score
                # добовляем слово в новую строку
                if score >= threshold:
                    s += " " + word + x
            # возвращаем слово или False
            if s == "":
                return False
            x1 = len(words.split(" ")) / 2
            x2 = len(s.split(" ")) - 1
            if x1 < x2:
                return words
            return False

        self.df["text"] = self.df["text"].apply(del_spec_sim)
        self.df["text"] = self.df["text"].apply(found_unrus_conves)
        self.df = self.df[self.df["text"] != False]
        self.df["text"] = self.df["text"].apply(found_trash_words)
        self.df = self.df[self.df["text"] != False]

    def vectorize(self):
        """Алгоритм векторизации предложений, подлежащих анализу"""

        df1 = pd.DataFrame(columns=["pred"])
        for i in range(len(self.df)):
            doc = self.nlp(str(self.df["text"].iloc[i]))
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
            X.toarray().transpose(), self.vectorizer.get_feature_names_out()
        )
        self.scaler.fit(vectors)
        vectors = self.scaler.transform(vectors).transpose()
        return vectors

    def clustersing(self, vectors):
        """Модуль кластеризации предложений"""

        def HKA(arr):
            """Кластеризация векторов, построенных на предложениях

            Args:
                arr (pandas.core.frame.DataFrame): датафрэйм векторных представлений каждого предложения

            Returns:
                klasters (numpy.ndarray): массив, содержащий номера кластеров на позициях, соответствующих позициям предложений в фрейме данных
            """

            samples = arr
            for i in range(len(samples)):
                if samples[i].sum() == 0:
                    samples[i][0] = 10 ** (-20)
            klasters = linkage(samples, method="complete", metric="cosine")
            return fcluster(klasters, 0.9, criterion="distance")

        def otchet_IKA(clusters_hier, df_clear):
            """Формирование кластеров предложений

            Args:
                clusters_hier (numpy.ndarray): массив, содержащий номера кластеров на позициях, соответствующих позициям предложений в фрейме данных
                df_clear (pandas.core.frame.DataFrame)
            """

            clusters = dict()
            df_clear["index"] = [i for i in range(len(df_clear))]
            for i in range(len(clusters_hier)):
                inf = df_clear.loc[df_clear["index"] == i, ["text", "date"]].iloc[0]
                if clusters_hier[i] in clusters.keys():
                    clusters[clusters_hier[i]].append([inf["text"], inf["date"]])
                else:
                    clusters[clusters_hier[i]] = [[inf["text"], inf["date"]]]
            clusters[-1] = [1]
            while True:
                for i in clusters.keys():
                    if len(clusters[i]) < 3:
                        clusters.pop(i)
                        break
                if i == -1:
                    break
            return clusters

        klasters_HKA = HKA(vectors)
        clusters = otchet_IKA(klasters_HKA, self.df)
        return clusters

    def FMW_rake(self, arr):
        """Модуль формирования ключевых слов по списку предложений

        Args:
            arr (list): список предолжений, по которым нужно составить ключевые слова

        Returns:
            kw (): список ключевых слов
        """

        s = ""
        for i in arr:
            s += ". " + i
        result = ""
        self.rake.extract_keywords_from_text(s)
        for i in self.rake.get_ranked_phrases()[:10]:
            result += i + ", "
        return result

    def get_data(self, clusters):
        """Форматирование кластеров для визуализации

        Returns:
            data (list[tuple]): список кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        data = []
        for i in clusters.keys():
            conv = []
            date = "2024-01-01"
            for j in clusters[i]:
                conv.append(j[0])
                if date < j[1]:
                    date = j[1]
            data.append((conv, self.FMW_rake(conv), date))
        data = sorted(data, key=lambda dt: len(dt[0]), reverse=True)
        return data

    def get_clusters_keywords(self, questions: list) -> list:  # type: ignore
        """Логика кластеризации текстовых данных

        Args:
            questions (list[QuestionAnswer]): список вопросов, подлежащих анализу

        Return:
            data (list[tuple]): список кортежей, для каждого: список вопросов, список ключевых слов, дата самого свежего вопроса
        """

        self.init_dataset(questions)
        self.preprocessing()
        vectors = self.vectorize()
        clusters = self.clustersing(vectors)
        return self.get_data(clusters)
