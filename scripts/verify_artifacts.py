"""Cross-check bundled results without retraining."""
import json,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score,confusion_matrix,average_precision_score
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'artifacts/metrics.json').read_text());p=pd.read_csv(ROOT/'artifacts/test_predictions.csv')
assert len(p)==r['ml']['n']
assert np.isclose(f1_score(p.y,p.probability>=.5),r['ml']['f1'])
assert np.isclose(average_precision_score(p.y,p.probability),r['ml']['pr_auc'])
assert confusion_matrix(p.y,p.probability>=.5).tolist()==r['ml']['confusion_matrix']
assert set(p.patient_id)==set(r['split']['test'])
print('Metrics match saved test predictions; test identities match partition manifest.')
