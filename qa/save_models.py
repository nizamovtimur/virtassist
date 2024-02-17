from sentence_transformers import SentenceTransformer

model_checkpoint = "nizamovtimur/rubert-tiny2-wikiutmn-gigachat-qa"
save_path = "saved_models/rubert-tiny2-wikiutmn-gigachat-qa"

model = SentenceTransformer(model_checkpoint)
model.save(save_path)