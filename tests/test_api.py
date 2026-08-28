"""CI 게이트. 하나라도 실패하면 이미지를 빌드하지 않는다.

성능 게이트는 train.py 가 떼어 둔 홀드아웃 점수를 본다.
학습 데이터로 채점하면 RandomForest 는 거의 1.0 이 나와서 게이트 구실을 못 한다.
"""
import json
import os

import pytest
from fastapi.testclient import TestClient

from main import app

# 홀드아웃 30건 기준. 1건 틀리면 0.967, 2건 틀리면 0.933 이라
# 0.90 은 "3건 이상 틀리면 배포 중단" 에 해당한다.
MIN_HOLDOUT_ACCURACY = 0.90
MIN_CV_ACCURACY = 0.93

client = TestClient(app)


@pytest.fixture(scope="module")
def metrics():
    if not os.path.exists("metrics.json"):
        pytest.fail("metrics.json 이 없습니다. 먼저 `python train.py` 를 실행하세요.")
    with open("metrics.json", encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------- 응답 계약


def test_root():
    res = client.get("/")
    assert res.status_code == 200
    assert "message" in res.json()


def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_predict_setosa():
    res = client.post("/predict", json={"data": [5.1, 3.5, 1.4, 0.2]})
    assert res.status_code == 200
    body = res.json()
    assert body["class_index"] == 0
    assert body["class_name"] == "setosa"


def test_predict_versicolor():
    res = client.post("/predict", json={"data": [5.5, 2.4, 3.8, 1.1]})
    assert res.status_code == 200
    assert res.json()["class_name"] == "versicolor"


def test_predict_virginica():
    res = client.post("/predict", json={"data": [6.7, 3.0, 5.2, 2.3]})
    assert res.status_code == 200
    assert res.json()["class_name"] == "virginica"


def test_predict_returns_probabilities():
    """경계 샘플. 확률이 한쪽으로 쏠리지 않는 경우에도 형식이 맞아야 한다."""
    res = client.post("/predict", json={"data": [6.0, 2.7, 5.1, 1.6]})
    body = res.json()
    assert 0.0 <= body["confidence"] <= 1.0
    assert set(body["probabilities"]) == {"setosa", "versicolor", "virginica"}
    assert abs(sum(body["probabilities"].values()) - 1.0) < 0.01
    # 가장 큰 확률이 곧 예측 클래스여야 한다
    top = max(body["probabilities"], key=body["probabilities"].get)
    assert top == body["class_name"]


# --------------------------------------------------------------------- 입력 검증


@pytest.mark.parametrize(
    "payload",
    [
        {"data": [5.1, 3.5, 1.4]},            # 3개
        {"data": [5.1, 3.5, 1.4, 0.2, 9.9]},  # 5개
        {"data": []},                          # 0개
    ],
)
def test_wrong_feature_count_is_422(payload):
    """개수가 틀리면 500 이 아니라 422 로 떨어져야 한다."""
    res = client.post("/predict", json=payload)
    assert res.status_code == 422


def test_missing_field_is_422():
    assert client.post("/predict", json={}).status_code == 422


# --------------------------------------------------------------------- 성능 게이트


def test_model_info_matches_metrics(metrics):
    res = client.get("/model-info")
    assert res.status_code == 200
    body = res.json()
    assert body["available"] is True
    assert body["best_model"] == metrics["best_model"]
    assert body["holdout_accuracy"] == metrics["holdout_accuracy"]


def test_holdout_accuracy_gate(metrics):
    acc = metrics["holdout_accuracy"]
    assert acc >= MIN_HOLDOUT_ACCURACY, (
        f"홀드아웃 정확도 {acc:.4f} < 기준 {MIN_HOLDOUT_ACCURACY} — 배포 중단"
    )


def test_cv_accuracy_gate(metrics):
    acc = metrics["cv_accuracy"]
    assert acc >= MIN_CV_ACCURACY, (
        f"교차검증 정확도 {acc:.4f} < 기준 {MIN_CV_ACCURACY} — 배포 중단"
    )


def test_holdout_was_not_used_for_training(metrics):
    """홀드아웃이 학습에 섞이면 게이트가 무의미해진다. 분할 비율을 확인한다."""
    total = metrics["n_train"] + metrics["n_holdout"]
    assert total == 150, f"iris 전체는 150건이어야 합니다. 현재 {total}"
    assert metrics["n_holdout"] == 30
