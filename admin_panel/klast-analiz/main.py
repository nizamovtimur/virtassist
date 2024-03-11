import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from database import QuestionAnswer
from os import environ
from dotenv import load_dotenv
import pymorphy2
# TF-IDF
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
# doc2vec
from gensim.models.doc2vec import Doc2Vec, TaggedDocument
from gensim.models import doc2vec
# иерархическая кластеризация
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
# кластеризация DBSCAN
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from kneed import KneeLocator

load_dotenv(dotenv_path="../virtassist/.env")
nlp = spacy.load("ru_core_news_sm")


def import_question_1():
    return np.array(
        ['Как получить справку об обучении?', 'Где взять справку о размере стипендии?', 'Как закрыть физру?',
         'Куда отнести справку для закрытия физры через тренажёрку?', 'До скольки работает столовая?',
         'когда закрывается столовка?', 'Где находятся корпуса?', 'как дойти до матфака?', 'как закрыть сессию',
         'когда начинается сдача сессий', 'когда зачётная неделя', 'как перевестись на другое направление',
         'как перевестись в другой ВУЗ?', 'как получить повышенную стипендию',
         'я слетел со стипы, как её вернуть?', 'какие есть стипендии?'])


def import_question():  # Заапрос из БД. Запрашивает вопросы с ответом "Ответ не найден."
    engine = create_engine(
        f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}")
    with Session(engine) as session:
        arr = np.array(session.query(QuestionAnswer.id, QuestionAnswer.answer, QuestionAnswer.question).filter(
            QuestionAnswer.answer == 'Ответ не найден.').all())[:, 2]
        session.commit()
    for i in range(len(arr)):
        if '\\n' in arr[i] or '\\t' in arr[i]:
            arr[i] = arr[i].replace('\\t', ' ').replace('\\n', ' ')
    return arr


def found_trash_words(words):  # Ищет мусорные слова
    threshold = 0.6
    s = ''
    morph = pymorphy2.MorphAnalyzer()

    SpecWords = ["тюмгу", "шкн", "игип", "фэи", "соцгум", "ипип", "биофак", "инзем", "инхим", "фти", "инбио", "ифк",
                 "ед", "шпи"]
    z = ('.', ',', '!', '?')
    for word in words.split(' '):
        x = word[-1]
        if x in z:
            word = word[:-1]
        else:
            x = ''

        if word.lower() in SpecWords:
            score = 1
        else:
            p = morph.parse(word)
            score = p[0].score
        if score >= threshold:
            s += ' ' + word + x
    if s == '': return False
    x1 = len(words.split(' ')) / 2
    x2 = len(s.split(' ')) - 1
    if x1 < x2:
        return words
    return False


def str2vec_TFIDF(dataset):  # Перевод строки в вектор, TFIDF
    doc = nlp(str(dataset[0]))
    df = pd.DataFrame([" ".join([token.lemma_ for token in doc if not token.is_stop and token.pos_ != "PUNCT"])])
    df.columns = ['pred']
    for i in range(1, len(dataset)):
        doc = nlp(str(dataset[i]))
        df.loc[i] = [" ".join([token.lemma_ for token in doc if not token.is_stop and token.pos_ != "PUNCT"])]
    vectorizer = TfidfVectorizer(
        min_df=2
    )
    X = vectorizer.fit_transform(df.pred)
    vectorizer.get_feature_names_out()

    newDataFrame = pd.DataFrame(X.toarray().transpose(), vectorizer.get_feature_names_out())
    return newDataFrame


def str2vec_doc2vec(dataset):
    db_documents_lem = pd.Series(dataset)
    documents = [TaggedDocument(doc, [i]) for i, doc in enumerate([text.split() for text in db_documents_lem])]
    doc2vec_model = Doc2Vec(documents, vector_size=150, window=5, min_count=1, workers=4)

    documents = pd.DataFrame([]*len(dataset))
    for i in range(len(dataset)):
        documents[i] = doc2vec_model.infer_vector(dataset[i].split())
    return(documents)


def hierarhy_klast_analiz(arr):  # Иерархический кластерный анализ
    # TFIDF
    '''samples = arr.values
    klasters = linkage(samples, method='complete')
    print(klasters)
    print(np.mean(klasters[:, 2]))
    print(fcluster(klasters, 0.9, criterion='distance'))
    dendrogram(klasters)
    plt.show()'''
    # doc2vec
    samples = arr.values
    klasters = linkage(samples, method='complete')
    print(klasters)
    print(np.mean(klasters[:, 2]))
    print(fcluster(klasters, 0.9, criterion='distance'))
    dendrogram(klasters)
    plt.show()


def DBSCAN_klast_analiz(arr):  # DBSCAN
    df = arr.values
    nearest_neighbors = NearestNeighbors(n_neighbors=2)
    neighbors = nearest_neighbors.fit(df)

    distances, indices = neighbors.kneighbors(df)
    distances = np.sort(distances[:, -1], axis=0)

    i = np.arange(len(distances))
    knee = KneeLocator(i, distances, S=1, curve='convex', direction='increasing', interp_method='polynomial')
    fig = plt.figure(figsize=(5, 5))
    plt.plot(distances)
    plt.xlabel("Points")
    plt.ylabel("Distance")

    fig = plt.figure(figsize=(5, 5))
    knee.plot_knee()
    plt.xlabel("Points")
    plt.ylabel("Distance")

    dbscan_cluster = DBSCAN(eps=distances[knee.knee], min_samples=1)
    dbscan_cluster.fit(arr.values)
    # Number of Clusters
    labels = dbscan_cluster.labels_
    N_clus = len(set(labels)) - (1 if -1 in labels else 0)
    print('Количество кластеров: %d' % N_clus)
    # Identify Noise
    n_noise = list(dbscan_cluster.labels_).count(-1)
    print('Количество точек шума: %d' % n_noise)


def main():
    arr = import_question_1()
    for i in range(len(arr)):
        arr[i] = found_trash_words(arr[i])
    StopList = ['False']
    for ST in StopList:
        arr = np.delete(arr, np.where(arr == ST))
    arrVec = str2vec_TFIDF(arr)
#    arrVec = str2vec_doc2vec(arr)
    arrVec = arrVec.transpose()
#    hierarhy_klast_analiz(arrVec)
    DBSCAN_klast_analiz(arrVec)


if __name__ == '__main__':
    main()
