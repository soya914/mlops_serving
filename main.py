from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import numpy as np

app = FastAPI(title="Iris Classifier")

model = joblib.load("model.joblib")
CLASS_NAMES = ["setosa", "versicolor", "virginica"]


class InputData(BaseModel):
    data: list[float]  # [꽃받침 길이, 꽃받침 너비, 꽃잎 길이, 꽃잎 너비]


@app.get("/")
def root():
    return {"message": "Iris Classifier API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(item: InputData):
    arr = np.array(item.data).reshape(1, -1)
    idx = int(model.predict(arr)[0])
    return {"class_index": idx, "class_name": CLASS_NAMES[idx]}
