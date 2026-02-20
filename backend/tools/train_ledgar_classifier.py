"""
Train a baseline legal clause type classifier using LexGLUE LEDGAR.

This script intentionally uses a single-label baseline:
- LEDGAR is multi-label.
- We select one label per sample using strategy: first (default).

Output:
- HuggingFace model dir compatible with CLAUSE_CLASSIFIER_MODEL_PATH.
"""

from __future__ import annotations

import argparse
import os
from collections import Counter
from typing import Dict, List

import numpy as np
from datasets import load_dataset
from sklearn.metrics import accuracy_score, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="distilbert-base-uncased")
    parser.add_argument("--output-dir", default="models/ledgar_clause_classifier")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--single-label-strategy", default="first", choices=["first"])
    return parser.parse_args()


def select_label(label_list: List[int]) -> int:
    if not label_list:
        return -1
    return int(label_list[0])


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    return {
        "accuracy": accuracy_score(labels, preds),
        "f1_macro": f1_score(labels, preds, average="macro"),
    }


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    dataset = load_dataset("coastalcph/lex_glue", "ledgar")
    train_ds = dataset["train"]
    val_ds = dataset["validation"]

    # Build label universe from train split.
    label_counter = Counter()
    for item in train_ds:
        for label_id in item["labels"]:
            label_counter[int(label_id)] += 1

    label_ids = sorted(label_counter.keys())
    label2id: Dict[str, int] = {str(lid): i for i, lid in enumerate(label_ids)}
    id2label: Dict[int, str] = {i: str(lid) for i, lid in enumerate(label_ids)}

    def preprocess(batch):
        texts = batch["text"]
        raw_labels = batch["labels"]
        picked = []
        for labels in raw_labels:
            lid = select_label(labels)
            picked.append(label2id[str(lid)] if lid >= 0 else 0)
        tokenized = tokenizer(
            texts,
            truncation=True,
            max_length=args.max_length,
        )
        tokenized["labels"] = picked
        return tokenized

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    train_tok = train_ds.map(preprocess, batched=True, remove_columns=train_ds.column_names)
    val_tok = val_ds.map(preprocess, batched=True, remove_columns=val_ds.column_names)

    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_name,
        num_labels=len(label_ids),
        label2id=label2id,
        id2label=id2label,
    )

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        num_train_epochs=args.epochs,
        learning_rate=args.learning_rate,
        weight_decay=0.01,
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )

    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Saved LEDGAR classifier to: {args.output_dir}")


if __name__ == "__main__":
    main()

