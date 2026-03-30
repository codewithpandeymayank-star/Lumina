import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
import torch
from torch.utils.data import Dataset
import numpy as np

print("Loading data...")
def load_data(path):
    texts, labels = [], []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if ';' in line:
                text, label = line.rsplit(';', 1)
                texts.append(text)
                labels.append(label)
    return texts, labels

train_texts, train_labels = load_data('../data/train.txt')
val_texts, val_labels = load_data('../data/val.txt')
test_texts, test_labels = load_data('../data/test.txt')

le = LabelEncoder()
train_enc = le.fit_transform(train_labels)
val_enc = le.transform(val_labels)
test_enc = le.transform(test_labels)

print("Emotions found:", list(le.classes_))
print("Train size:", len(train_texts))

print("Loading tokenizer...")
tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
train_tok = tokenizer(train_texts, truncation=True, padding=True, max_length=64)
val_tok = tokenizer(val_texts, truncation=True, padding=True, max_length=64)
test_tok = tokenizer(test_texts, truncation=True, padding=True, max_length=64)

class EmotionDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __len__(self):
        return len(self.labels)
    def __getitem__(self, idx):
        item = {k: torch.tensor(v[idx]) for k, v in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

train_dataset = EmotionDataset(train_tok, train_enc)
val_dataset = EmotionDataset(val_tok, val_enc)
test_dataset = EmotionDataset(test_tok, test_enc)

print("Loading model...")
model = DistilBertForSequenceClassification.from_pretrained(
    'distilbert-base-uncased', num_labels=len(le.classes_))

args = TrainingArguments(
    output_dir='../model',
    num_train_epochs=1,
    per_device_train_batch_size=64,
    per_device_eval_batch_size=32,
    eval_strategy='epoch',
    save_strategy='epoch',
    load_best_model_at_end=True,
    logging_steps=50,
)

trainer = Trainer(
    model=model,
    args=args,
    train_dataset=train_dataset,
    eval_dataset=val_dataset,
)

print("Training started... this will take 15-20 minutes")
trainer.train()

print("Saving model...")
model.save_pretrained('../model/emotion_model')
tokenizer.save_pretrained('../model/emotion_model')

import pickle
with open('../model/label_encoder.pkl', 'wb') as f:
    pickle.dump(le, f)

print("Done! Model saved.")
preds = trainer.predict(test_dataset)
pred_labels = np.argmax(preds.predictions, axis=1)
print("Test Accuracy:", round(accuracy_score(test_enc, pred_labels) * 100, 2), "%")
