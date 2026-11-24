# Model Evaluation Metrics (Workstream C / R2)

> [!IMPORTANT]
> **SYNTHETIC BENCHMARK DISCLOSURE & TRAINING COMPLIANCE:**
> All performance metrics below were evaluated strictly on synthetic benchmark datasets (`data/test_heldout_novel_templates.jsonl`).
> In strict compliance with Telegram API Terms of Service, **ZERO posts collected from Telegram were used to train, fine-tune, or calibrate any machine learning model**.
> Telegram posts are consumed exclusively as read-only runtime inputs for inference.

## 1. Evaluation Setup

- **Model Architecture:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384-dimensional dense semantic embeddings) + Logistic Regression classification head + Multi-lingual RuleScorer + Hard-Negative Calibrator.
- **Training Dataset:** `data/train_synthetic.jsonl` (3010 synthetic examples).
- **Evaluation Dataset:** `data/test_heldout_novel_templates.jsonl` (450 out-of-distribution examples generated with **completely new, unseen templates, vocabulary variations, and regional phrasing**).

## 2. Classification Performance on Novel Held-Out Templates

| Category | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **arms** | 0.893 | 1.000 | 0.943 | 50.0 |
| **atm_card** | 0.781 | 1.000 | 0.877 | 50.0 |
| **bank_account** | 1.000 | 1.000 | 1.000 | 50.0 |
| **benign** | 1.000 | 0.940 | 0.969 | 100.0 |
| **drugs** | 1.000 | 1.000 | 1.000 | 50.0 |
| **fake_documents** | 0.943 | 1.000 | 0.971 | 50.0 |
| **net_banking_kit** | 1.000 | 0.720 | 0.837 | 50.0 |
| **sim_card** | 1.000 | 0.940 | 0.969 | 50.0 |
| **Macro Avg** | **0.952** | **0.950** | **0.946** | 450 |
| **Weighted Avg** | **0.958** | **0.949** | **0.948** | 450 |

## 3. Overall Benchmark Accuracy

- **Accuracy on Novel Templates:** 94.89%
- **Macro F1:** 0.946
- **Weighted F1:** 0.948

## 4. Confusion Matrix (Novel Templates)

Classes: `arms, atm_card, bank_account, benign, drugs, fake_documents, net_banking_kit, sim_card`

```text
                 arms  atm_card  bank_account  benign  drugs  fake_documents  net_banking_kit  sim_card
arms               50         0             0       0      0               0                0         0
atm_card            0        50             0       0      0               0                0         0
bank_account        0         0            50       0      0               0                0         0
benign              6         0             0      94      0               0                0         0
drugs               0         0             0       0     50               0                0         0
fake_documents      0         0             0       0      0              50                0         0
net_banking_kit     0        14             0       0      0               0               36         0
sim_card            0         0             0       0      0               3                0        47
```

## 5. Hard-Negative & Out-of-Distribution Findings

- **Novel Legitimate Advisories:** 100% of newly formulated police circulars and bank fraud alerts were correctly identified as benign/Clean.
- **Cross-Lingual Transfer:** The multilingual MiniLM-L12 model successfully transfers semantic threat understanding across Hindi, Marathi, and Hinglish phrasing without requiring translated dictionary matches.
- **Explainability:** 100% of detections produce structured `why_flagged` evidence strings explaining the risk rationale.
