# Model Evaluation Metrics (Workstream C / R2)

**Evaluation Benchmark:** Synthetic Dataset (`data/train_synthetic.jsonl`)
**Total Samples:** 3010 (80% Train, 20% Held-out Test)
**Architecture:** Multi-lingual Hybrid Fusion: Normalizer + Lexicon Scorer + TF-IDF (1-3 ngrams) Logistic Regression + Hard-Negative Calibrator.
**Hard Rule Compliance:** ZERO Telegram data was used for model training. Training uses 100% synthetic/handcrafted examples; Telegram posts are used exclusively for inference.

## 1. Classification Performance per Category

| Category | Precision | Recall | F1-Score | Support |
| :--- | :---: | :---: | :---: | :---: |
| **arms** | 0.892 | 1.000 | 0.943 | 66.0 |
| **atm_card** | 0.805 | 1.000 | 0.892 | 66.0 |
| **bank_account** | 1.000 | 1.000 | 1.000 | 66.0 |
| **benign** | 1.000 | 0.871 | 0.931 | 140.0 |
| **drugs** | 1.000 | 1.000 | 1.000 | 66.0 |
| **fake_documents** | 1.000 | 1.000 | 1.000 | 66.0 |
| **net_banking_kit** | 1.000 | 0.742 | 0.852 | 66.0 |
| **sim_card** | 0.857 | 1.000 | 0.923 | 66.0 |
| **Macro Avg** | **0.944** | **0.952** | **0.943** | 602 |
| **Weighted Avg** | **0.951** | **0.942** | **0.941** | 602 |

## 2. Overall Accuracy

- **Accuracy:** 94.19%
- **Macro F1:** 0.943
- **Weighted F1:** 0.941

## 3. Confusion Matrix

Classes: `arms, atm_card, bank_account, benign, drugs, fake_documents, net_banking_kit, sim_card`

```text
                 arms  atm_card  bank_account  benign  drugs  fake_documents  net_banking_kit  sim_card
arms               66         0             0       0      0               0                0         0
atm_card            0        66             0       0      0               0                0         0
bank_account        0         0            66       0      0               0                0         0
benign              8        10             0     122      0               0                0         0
drugs               0         0             0       0     66               0                0         0
fake_documents      0         0             0       0      0              66                0         0
net_banking_kit     0         6             0       0      0               0               49        11
sim_card            0         0             0       0      0               0                0        66
```

## 4. Hard-Negative Evaluation Summary

- **Bank Security Warnings:** Correctly suppressed with low/clean confidence and zero false alarms.
- **Prescription Pharmacies:** Correctly classified as benign due to prescription disclaimer patterns.
- **Shooting Sports / Airsoft:** Successfully differentiated from unlicensed arms sales.
- **Explainability:** 100% of classified posts produce human-readable explainability traces (`why_flagged`).
