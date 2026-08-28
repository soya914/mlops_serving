"""1~2일차에서 만든 것과 동일한 붓꽃 분류 모델을 학습해 model.joblib 으로 저장."""
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import joblib
import sklearn

X, y = load_iris(return_X_y=True)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X, y)
joblib.dump(model, "model.joblib")
print("saved model.joblib / sklearn", sklearn.__version__, "/ acc", model.score(X, y))
