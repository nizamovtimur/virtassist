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
    if len(words.split(' '))/2 > len(s.split(' ')):
        return s
    return False

def str2vec(): # Перевод строки в вектор, TFIDF
    from sklearn.feature_extraction.text import TfidfVectorizer
    import spacy
    import pandas as pd
    nlp = spacy.load("ru_core_news_sm")

    def preprocessing(text: str) -> str:
        doc = nlp(text)
        return " ".join([token.lemma_ for token in doc if not token.is_stop and token.pos_ != "PUNCT"])

    df = pd.DataFrame([preprocessing('проведём проверку этого алгоритма, поехали')])
    df.columns = ['pred']
    vectorizer = TfidfVectorizer()
    print(df.shape)
    X = vectorizer.fit_transform(df.pred)
    vectorizer.get_feature_names_out()
    print(X)

def importQuestion(): # Заапрос из БД. Пока не работает
    from sqlalchemy import and_, create_engine, func, select
    from sqlalchemy.orm import Session
    from loguru import logger
    #================================================================
    import db_session
    from database import User, QuestionAnswer
    #================================================================
    db_session.global_init('sqlite:///sqlite3.db')
    session = db_session.create_session()
    for i in session.query(QuestionAnswer.id, QuestionAnswer.question, QuestionAnswer.answer).filter(QuestionAnswer.id == 1).all():
        print(i)
importQuestion()
