import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
import spacy
import pandas as pd
nlp = spacy.load("ru_core_news_sm")
def FoundTrashWords(words): # Ищет мусорные слова
    import pymorphy2
    threshold = 0.6
    s = ''
    morph = pymorphy2.MorphAnalyzer()

    z = ('.', ',', '!', '?')
    for word in words.split(' '):
        x = word[-1]
        if x in z:
            word = word[:-1]
        else:
            x = ''

        p = morph.parse(word)
        score = p[0].score
        if score >= threshold:
            s+=' ' + word+x
    if s == '': return False
    x1 = len(words.split(' '))/2
    x2 = len(s.split(' ')) - 1
    if x1 < x2:
        return words
    return False

def str2vec(string): # Перевод строки в вектор, TFIDF
    string = str(string)
    def preprocessing(text: str) -> str:
        doc = nlp(text)
        return " ".join([token.lemma_ for token in doc if not token.is_stop and token.pos_ != "PUNCT"])

    df = pd.DataFrame([preprocessing(string)])
    df.columns = ['pred']
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(df.pred)
    vectorizer.get_feature_names_out()
    return X

def importQuestion(): # Заапрос из БД. Запрашивает вопросы с ответом "Ответ не найден."
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from database import QuestionAnswer
    from os import environ
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="../virtassist/.env")

    engine = create_engine(f"postgresql://{environ.get('POSTGRES_USER')}:{environ.get('POSTGRES_PASSWORD')}@{environ.get('POSTGRES_HOST')}/{environ.get('POSTGRES_DB')}")
    with Session(engine) as session:
        arr = np.array(session.query(QuestionAnswer.id, QuestionAnswer.answer, QuestionAnswer.question).filter(QuestionAnswer.answer == 'Ответ не найден.').all())[:,2]
        session.commit()
    return arr

if __name__ == '__main__':
    arr = importQuestion()
    for i in range(len(arr)):
        arr[i] = FoundTrashWords(arr[i])
    StopList = ['False']
    for ST in StopList:
        arr = np.delete(arr, np.where(arr == ST))
    arr_vec = np.array([str2vec(arr[0])])
    for i in range(1, len(arr)):
        try:
            arr_vec = np.append(arr_vec, str2vec(arr[i]))
        except:
            print(arr[i])
    print(arr_vec)
