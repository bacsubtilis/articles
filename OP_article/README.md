# OP Article — Synthetic Data Equivalence for Low-BMD Prediction

Short experiment accompanying my LinkedIn article: **[TODO: LinkedIn article URL]**

Using NHANES cohorts (development 2017–2020, external validation 2013–2014), we predict low bone mineral density in an experiment whose clinical setting and feature palette are **inspired by** Xu et al. (2024)—not a strict replication. TARGET is defined from femoral-neck T-score only; participants with self-reported osteoporosis (`OSQ060 = Yes`) but normal BMD are discarded, and `OSQ060` is never used as a feature. CTGAN generates synthetic training data from the real train fold only. We then compare three training arms—**real (R)**, **synthetic (S)**, and **augmented (R+S)**—on real internal and external test sets, and use SHAP on logistic regression to check whether feature importance stays consistent across arms.

## Pipeline

| Notebook | Step |
|----------|------|
| `1_DATA_GATHERING.ipynb` | Build development & external cohorts from NHANES |
| `2_DATA_CLEANING.ipynb` | Complete-case cleaning and TARGET definition |
| `3_DATA_SPLITTING.ipynb` | Stratified 70/30 train–test split |
| `4_CTGAN_SYNTHETIC.ipynb` | Train CTGAN and sample a synthetic pool |
| `5_MODELS_EQUIVALENCE.ipynb` | Compare R / S / R+S model performance |
| `6_LR_SHAP_ANALYSIS.ipynb` | SHAP interpretability for logistic regression |

Shared helpers live in `experiment_utils.py`.
