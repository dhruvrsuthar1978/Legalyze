"""
Fine-tune a QA model on CUAD-style SQuAD JSON.

Expected input format:
- Standard SQuAD v1 JSON with data -> paragraphs -> qas -> answers.

This script does not download CUAD automatically.
Point --train-file / --validation-file to prepared JSON files.
"""

from __future__ import annotations

import argparse
import os

from datasets import load_dataset
from transformers import (
    AutoModelForQuestionAnswering,
    AutoTokenizer,
    DefaultDataCollator,
    Trainer,
    TrainingArguments,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-name", default="deepset/roberta-base-squad2")
    parser.add_argument("--train-file", required=True)
    parser.add_argument("--validation-file", required=True)
    parser.add_argument("--output-dir", default="models/cuad_qa_model")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=384)
    parser.add_argument("--doc-stride", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    ds = load_dataset(
        "json",
        data_files={"train": args.train_file, "validation": args.validation_file},
        field="data",
    )

    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def flatten_examples(example):
        rows = {"id": [], "context": [], "question": [], "answers": []}
        for item in example:
            for para in item["paragraphs"]:
                context = para["context"]
                for qa in para["qas"]:
                    rows["id"].append(qa["id"])
                    rows["context"].append(context)
                    rows["question"].append(qa["question"])
                    rows["answers"].append(qa["answers"])
        return rows

    train_flat = ds["train"].map(flatten_examples, batched=True, remove_columns=ds["train"].column_names)
    val_flat = ds["validation"].map(flatten_examples, batched=True, remove_columns=ds["validation"].column_names)

    def preprocess(examples):
        tokenized = tokenizer(
            examples["question"],
            examples["context"],
            truncation="only_second",
            max_length=args.max_length,
            stride=args.doc_stride,
            return_overflowing_tokens=True,
            return_offsets_mapping=True,
            padding="max_length",
        )

        sample_mapping = tokenized.pop("overflow_to_sample_mapping")
        offset_mapping = tokenized.pop("offset_mapping")

        start_positions = []
        end_positions = []

        for i, offsets in enumerate(offset_mapping):
            sample_idx = sample_mapping[i]
            answer = examples["answers"][sample_idx]
            if len(answer["answer_start"]) == 0:
                start_positions.append(0)
                end_positions.append(0)
                continue

            start_char = answer["answer_start"][0]
            end_char = start_char + len(answer["text"][0])

            sequence_ids = tokenized.sequence_ids(i)
            context_start = 0
            while sequence_ids[context_start] != 1:
                context_start += 1
            context_end = len(sequence_ids) - 1
            while sequence_ids[context_end] != 1:
                context_end -= 1

            if offsets[context_start][0] > start_char or offsets[context_end][1] < end_char:
                start_positions.append(0)
                end_positions.append(0)
            else:
                idx = context_start
                while idx <= context_end and offsets[idx][0] <= start_char:
                    idx += 1
                start_positions.append(idx - 1)

                idx = context_end
                while idx >= context_start and offsets[idx][1] >= end_char:
                    idx -= 1
                end_positions.append(idx + 1)

        tokenized["start_positions"] = start_positions
        tokenized["end_positions"] = end_positions
        return tokenized

    train_tok = train_flat.map(preprocess, batched=True, remove_columns=train_flat.column_names)
    val_tok = val_flat.map(preprocess, batched=True, remove_columns=val_flat.column_names)

    model = AutoModelForQuestionAnswering.from_pretrained(args.model_name)

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
        report_to=[],
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_tok,
        eval_dataset=val_tok,
        tokenizer=tokenizer,
        data_collator=DefaultDataCollator(),
    )

    trainer.train()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    print(f"Saved CUAD QA model to: {args.output_dir}")


if __name__ == "__main__":
    main()

