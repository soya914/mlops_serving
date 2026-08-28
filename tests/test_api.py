"""CI 게이트. 여기서 실패하면 이미지를 빌드하지 않는다."""
import joblib
from fastapi.testclient import TestClient
from sklearn.datasets import load_iris

from main import app

client = TestClient(app)


def test_root():
    res = client.get("/")
    assert res.status_code == 200


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_predict_setosa():
    res = client.post("/predict", json={"data": [5.1, 3.5, 1.4, 0.2]})
    assert res.status_code == 200
    assert res.json() == {"class_index": 0, "class_name": "setosa"}


def test_predict_virginica():
    res = client.post("/predict", json={"data": [6.7, 3.0, 5.2, 2.3]})
    assert res.status_code == 200
    assert res.json()["class_name"] == "virginica"


def test_model_accuracy():
    """성능이 떨어진 모델이 배포되는 걸 막는 품질 게이트."""
    model = joblib.load("model.joblib")
    X, y = load_iris(return_X_y=True)
    acc = model.score(X, y)
    assert acc >= 0.95, f"정확도 {acc:.3f} 로 기준(0.95) 미달 — 배포 중단"
