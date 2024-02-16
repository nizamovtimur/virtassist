from sentence_transformers import SentenceTransformer

model_checkpoint = "Den4ikAI/rubert-tiny2-retriever"
save_path = "saved_models/rubert-tiny2-retriever"

model = SentenceTransformer(model_checkpoint)
model.save(save_path)