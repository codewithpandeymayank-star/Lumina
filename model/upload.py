from huggingface_hub import login, HfApi
login(token="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")
api = HfApi()
api.upload_file(
    path_or_fileobj="label_encoder.pkl",
    path_in_repo="label_encoder.pkl",
    repo_id="GabbarM32/emotion-chatbot-model",
    repo_type="model"
)
print("label_encoder.pkl uploaded!")
