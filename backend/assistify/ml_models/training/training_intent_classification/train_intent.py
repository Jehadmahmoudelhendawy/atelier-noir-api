import os
import json
import logging
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from torch.utils.data import Dataset
from sklearn.model_selection import train_test_split
from .training_data import TRAINING_DATA, INTENT_MAP
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
class IntentDataset(Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels
    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item
    def __len__(self):
        return len(self.labels)
def main():
    model_name = "UBC-NLP/MARBERTv2"
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../intent_classification/intent_model_finetuned'))
    logger.info(f"Loading tokenizer for {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    texts = [item[0] for item in TRAINING_DATA]
    labels = [INTENT_MAP[item[1]] for item in TRAINING_DATA]
    train_texts, val_texts, train_labels, val_labels = train_test_split(texts, labels, test_size=0.2, random_state=42)
    logger.info("Tokenizing dataset...")
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=128)
    train_dataset = IntentDataset(train_encodings, train_labels)
    val_dataset = IntentDataset(val_encodings, val_labels)
    num_labels = len(INTENT_MAP)
    logger.info(f"Loading base model {model_name} with {num_labels} labels")
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=50,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
    )
    logger.info("Starting training (This might take a while on CPU)...")
    trainer.train()
    logger.info(f"Saving fine-tuned model to {output_dir}")
    os.makedirs(output_dir, exist_ok=True)
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    config = {
        'intent_map': INTENT_MAP,
        'num_labels': num_labels
    }
    with open(os.path.join(output_dir, 'intent_config.json'), 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    logger.info("✅ Training complete and model saved successfully!")
if __name__ == "__main__":
    main()
