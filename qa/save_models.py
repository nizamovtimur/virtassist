from sentence_transformers import SentenceTransformer

model_checkpoint = "nizamovtimur/rubert-tiny2-wikiutmn"
save_path = "saved_models/rubert-tiny2-wikiutmn"

model = SentenceTransformer(model_checkpoint)
model.save(save_path)