"""후보 모델을 교차검증으로 비교해 가장 좋은 것 하나만 저장한다.

산출물 2개:
  - model.joblib   서빙에 쓸 모델
  - metrics.json   무엇을 왜 골랐는지 + 성능 (CI 게이트와 /model-info 가 읽는다)

이전 버전은 전체 데이터로 학습한 뒤 같은 데이터로 채점했다.
RandomForest 는 그 경우 거의 항상 1.0 이 나와서 성능 게이트가 아무것도 막지 못한다.
그래서 홀드아웃을 떼고, 모델 선택은 학습셋 안에서만 교차검증으로 한다.
"""
import json
from datetime import datetime, timezone

import joblib
import sklearn
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

RANDOM_STATE = 42
TEST_SIZE = 0.2
N_SPLITS = 5

CLASS_NAMES = ["setosa", "versicolor", "virginica"]
FEATURE_NAMES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]

CANDIDATES = {
    "random_forest_100": RandomForestClassifier(
        n_estimators=100, random_state=RANDOM_STATE
    ),
    "random_forest_300_depth3": RandomForestClassifier(
        n_estimators=300, max_depth=3, random_state=RANDOM_STATE
    ),
    "logistic_regression": make_pipeline(
        StandardScaler(),
        LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    ),
}


def main():
    X, y = load_iris(return_X_y=True)

    # 홀드아웃은 학습에도, 모델 선택에도 절대 쓰지 않는다.
    X_train, X_holdout, y_train, y_holdout = train_test_split(
        X, y, test_size=TEST_SIZE, stratify=y, random_state=RANDOM_STATE
    )

    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    print(f"후보 {len(CANDIDATES)}개를 {N_SPLITS}-fold 교차검증으로 비교합니다.")
    print(f"학습 {len(X_train)}건 / 홀드아웃 {len(X_holdout)}건\n")

    cv_scores = {}
    for name, model in CANDIDATES.items():
        scores = cross_val_score(model, X_train, y_train, cv=cv, scoring="accuracy")
        cv_scores[name] = float(scores.mean())
        print(f"  {name:26s} CV {scores.mean():.4f}  (±{scores.std():.4f})")

    best_name = max(cv_scores, key=cv_scores.get)
    best_model = CANDIDATES[best_name].fit(X_train, y_train)
    holdout_accuracy = float(best_model.score(X_holdout, y_holdout))

    print(f"\n선택된 모델: {best_name}")
    print(f"  CV 정확도      {cv_scores[best_name]:.4f}")
    print(f"  홀드아웃 정확도 {holdout_accuracy:.4f}  ← 한 번도 안 본 데이터")

    joblib.dump(best_model, "model.joblib")

    metrics = {
        "best_model": best_name,
        "cv_accuracy": round(cv_scores[best_name], 4),
        "holdout_accuracy": round(holdout_accuracy, 4),
        "cv_accuracy_all_candidates": {k: round(v, 4) for k, v in cv_scores.items()},
        "n_train": len(X_train),
        "n_holdout": len(X_holdout),
        "cv_folds": N_SPLITS,
        "random_state": RANDOM_STATE,
        "class_names": CLASS_NAMES,
        "feature_names": FEATURE_NAMES,
        "sklearn_version": sklearn.__version__,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    with open("metrics.json", "w", encoding="utf-8") as fh:
        json.dump(metrics, fh, ensure_ascii=False, indent=2)

    print("\nmodel.joblib / metrics.json 저장 완료")


if __name__ == "__main__":
    main()
