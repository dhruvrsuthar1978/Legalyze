# Model Training Runbook

This project can use fine-tuned legal models in addition to default keyword logic.

## 1) Install training dependencies

```bash
pip install datasets accelerate scikit-learn
```

## 2) Train clause classifier (LEDGAR)

```bash
cd backend
python tools/train_ledgar_classifier.py \
  --model-name distilbert-base-uncased \
  --output-dir models/ledgar_clause_classifier \
  --epochs 2 \
  --batch-size 8
```

## 3) Enable classifier in backend

Set these in `backend/.env`:

```env
CLAUSE_CLASSIFIER_MODEL_PATH=models/ledgar_clause_classifier
CLAUSE_CLASSIFIER_MIN_CONFIDENCE=0.55
```

Restart backend.

## 4) Fine-tune QA model for CUAD (optional)

Prepare CUAD in SQuAD JSON format, then run:

```bash
cd backend
python tools/train_cuad_qa.py \
  --train-file data/cuad/train.json \
  --validation-file data/cuad/validation.json \
  --output-dir models/cuad_qa_model \
  --epochs 2 \
  --batch-size 8
```

## Notes

- If `CLAUSE_CLASSIFIER_MODEL_PATH` is missing, the app automatically falls back to existing keyword clause classification.
- Current LEDGAR script is a baseline single-label approach to get production wiring in place quickly.
