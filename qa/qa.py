from aiohttp import web
from langchain.document_loaders import DataFrameLoader
from langchain.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.vectorstores import FAISS
import pandas as pd
from config import Config


routes = web.RouteTableDef()
documents = pd.read_csv("departments.csv", index_col=0).dropna(ignore_index=True)
documents.columns = ["institution", "department", "url", "description"]
loader = DataFrameLoader(documents, page_content_column='description')
loaded_documents = loader.load()
embeddings = HuggingFaceInferenceAPIEmbeddings(
    api_key=Config.HUGGINGFACE_TOKEN,
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)
db = FAISS.from_documents(loaded_documents, embeddings)
db.as_retriever()
db.save_local('faiss_index')


@routes.post('/')
async def main(request):
    question = (await request.json())['question']
    found_doc = db.similarity_search(question)[0].dict()
    department = found_doc['metadata']['department']
    source = found_doc['metadata']['url']
    return web.Response(text=f"Возможно, тебе стоит обраться в {department}. Подробнее: {source}")


app = web.Application()
app.add_routes(routes)
web.run_app(app)
