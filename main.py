"""붓꽃 분류 서빙 API.

train.py 가 만든 model.joblib 을 읽어 예측을 제공한다.
metrics.json 이 함께 있으면 /model-info 로 "지금 무슨 모델이 서빙 중인지" 를 노출한다.
"""
import json
from typing import Optional

import joblib
import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel, Field, field_validator

MODEL_PATH = "model.joblib"
METRICS_PATH = "metrics.json"

CLASS_NAMES = ["setosa", "versicolor", "virginica"]
FEATURE_NAMES = ["꽃받침 길이", "꽃받침 너비", "꽃잎 길이", "꽃잎 너비"]

app = FastAPI(
    title="Iris Classifier",
    description="붓꽃 치수 4개로 품종을 예측하는 API",
    version="1.1.0",
)

model = joblib.load(MODEL_PATH)


def _load_metrics() -> Optional[dict]:
    """metrics.json 은 없어도 서비스는 떠야 한다. 실패하면 None."""
    try:
        with open(METRICS_PATH, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return None


METRICS = _load_metrics()


class InputData(BaseModel):
    data: list[float] = Field(
        ...,
        description="[꽃받침 길이, 꽃받침 너비, 꽃잎 길이, 꽃잎 너비] (cm)",
        json_schema_extra={"example": [5.1, 3.5, 1.4, 0.2]},
    )

    @field_validator("data")
    @classmethod
    def _exactly_four_features(cls, value: list[float]) -> list[float]:
        # 개수가 틀리면 sklearn 안에서 터져 500 이 난다. 여기서 막아 422 로 돌려준다.
        if len(value) != 4:
            raise ValueError(
                f"data 는 값 4개여야 합니다 ({', '.join(FEATURE_NAMES)}). 받은 개수: {len(value)}"
            )
        return value


@app.get("/", summary="서버 생존 확인")
def root():
    return {"message": "Iris Classifier API is running", "version": app.version}


@app.get("/health", summary="헬스체크")
def health():
    return {"status": "ok"}


@app.get("/model-info", summary="서빙 중인 모델 정보")
def model_info():
    """CD 가 배포한 이미지에 어떤 모델이 들어 있는지 확인하는 용도."""
    if METRICS is None:
        return {"available": False, "reason": "metrics.json 없음"}
    return {
        "available": True,
        "best_model": METRICS.get("best_model"),
        "cv_accuracy": METRICS.get("cv_accuracy"),
        "holdout_accuracy": METRICS.get("holdout_accuracy"),
        "sklearn_version": METRICS.get("sklearn_version"),
        "trained_at": METRICS.get("trained_at"),
    }


@app.post("/predict", summary="품종 예측")
def predict(item: InputData):
    arr = np.array(item.data).reshape(1, -1)
    idx = int(model.predict(arr)[0])

    result = {"class_index": idx, "class_name": CLASS_NAMES[idx]}

    # 확률을 못 내는 모델로 바뀌어도 예측 자체는 계속 동작해야 한다.
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(arr)[0]
        result["confidence"] = round(float(proba[idx]), 4)
        result["probabilities"] = {
            name: round(float(p), 4) for name, p in zip(CLASS_NAMES, proba)
        }

    return result
