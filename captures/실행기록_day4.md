# 4일차 CI/CD — 실행 기록

기록 시각: 2026-08-28 14:10 (KST)

| 항목 | 값 |
|---|---|
| 레포 | https://github.com/soya914/mlops_serving (public) |
| 워크플로 | `.github/workflows/main.yml` — job 3개 |
| 이미지 | `soya14/iris-classifier`, `soya14/iris-frontend` |
| 배포 대상 | GCP `bold-guru-501604-b2` / `iris-vm` (us-central1-a, e2-micro) |
| 성공한 실행 | `#10` (3m 13s), `#11` (1m 39s) — 연속 2회 |

---

## 1. 파이프라인 구조

```
git push (main)
  │
  ├─ [1] 학습 & 테스트        후보 3개 5-fold CV 비교 → 최고 모델 저장 → 테스트 14개
  │        실패 시 → 빌드하지 않음
  │
  ├─ [2] 이미지 빌드 & 푸시   백엔드·프론트 2개 → Docker Hub (:latest, :커밋해시)
  │        실패 시 → 배포하지 않음
  │
  └─ [3] GCP VM 배포          SSH → pull → 컨테이너 교체 → 내부 health → 외부 /predict
           실패 시 → 워크플로 실패
```

학습 산출물(`model.joblib`, `metrics.json`)은 artifact 로 [1] → [2] 로 전달된다.
레포에 커밋된 파일이 아니라 **러너가 방금 만든 모델**이 이미지에 들어간다.

---

## 2. 실행 결과

### 성공한 실행 2회

| # | 커밋 | 소요 | 결과 |
|---|---|---|---|
| 10 | `97429ba` | 3m 13s | ✅ 학습 28s / 빌드 1m32s / 배포 1m04s |
| 11 | `4f8425c` | 1m 39s | ✅ (빌드 캐시가 살아 있어 단축) |

11번은 README 커밋으로 **자동 트리거**된 것이다. 손으로 배포한 것이 아니라
푸시만으로 배포까지 갔다는 증거가 된다.

### 배포된 모델이 방금 학습한 것인지

`/model-info` 의 `trained_at` 으로 확인한다.

| 실행 | 푸시 시각(UTC) | `trained_at`(UTC) |
|---|---|---|
| #10 | 03:48:30 | **03:48:55** |
| #11 | 03:55:__ | **03:55:58** |

푸시할 때마다 학습 시각이 갱신된다. 커밋해시 태그도 함께 붙어 어느 코드가 도는지 특정된다.

### 모델 선택 결과 (실행 #11 기준)

```
random_forest_100          CV 0.9500  (±0.0312)
random_forest_300_depth3   CV 0.9500  (±0.0312)
logistic_regression        CV 0.9583  (±0.0264)   ← 선택

홀드아웃 정확도 0.9333  (30건 중 28건, 게이트 0.90 통과)
```

홀드아웃 30건은 학습에도 모델 선택에도 쓰지 않았다.

---

## 3. 외부에서 확인한 배포 결과

서울에서 미국 아이오와 VM 으로 직접 호출 (2026-08-28 14:05 KST).

| 요청 | 응답 |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /model-info` | `logistic_regression` · CV `0.9583` · 홀드아웃 `0.9333` · `trained_at 03:55:58` |
| `POST /predict [5.1,3.5,1.4,0.2]` | `setosa`, confidence `0.9808` |
| `POST /predict [6.7,3.0,5.2,2.3]` | `virginica`, confidence `0.9565` |
| `POST /predict [6.7,3.0,5.2]` (값 3개) | `422` |
| Streamlit `:8501` | 화면 정상, **예측하기 클릭 → 결과 표시** |

Streamlit 버튼이 동작했다는 것은 프론트 컨테이너가 도커 브리지(`172.17.0.1`)로
백엔드 컨테이너를 호출하는 경로까지 살아 있다는 뜻이다.

---

## 4. 강의 자료와 다르게 한 부분

| 자료 | 실제 | 이유 |
|---|---|---|
| `file: ./dockerfile` | `./Dockerfile` | 리눅스 러너는 대소문자 구분. 그대로 두면 not found |
| 이미지 1개 | 2개 | 3일차에 백엔드+프론트를 같이 올렸으므로 |
| 이름으로 컨테이너 삭제 | 이름 + **포트 필터** | 3일차 컨테이너는 `--name` 없이 떠 있어 이름으로 안 지워짐 |
| 공개키 등록 단계 없음 | `gcloud compute instances add-metadata` | 없으면 `ssh: handshake failed` |
| `usermod -aG docker` | `sudo docker` 사용 | usermod 는 재로그인 필요해 CI 에서 한 번에 안 먹음 |
| 테스트 없음 | 테스트 14개 + 성능 게이트 | "오류가 없는지 확인" 이 CI 의 본질이라 |
| `:latest` 만 | `:latest` + `:커밋해시` | latest 만으로는 무엇이 도는지 특정 못 함 |

---

## 5. 실패했던 이력 (Actions 목록의 빨간 표시)

캡처 `31_actions_runs.png` 에 실패한 실행이 남아 있다. 숨기지 않고 기록한다.

| 실행 | 실패 원인 | 해결 |
|---|---|---|
| #1 | `ModuleNotFoundError: No module named 'main'` | 로컬은 `python -m pytest`(CWD 를 import 경로에 넣음), CI 는 `pytest`(안 넣음). `pytest.ini` 의 `pythonpath = .` 로 고정 |
| #2~#9 | `unauthorized: Password required` | `DOCKERHUB_TOKEN` 미등록. 토큰 발급 후 시크릿 등록으로 해결 |

`#10` 부터 전 구간 성공.

추가로 `#10` 에는 경고가 하나 있었다.

```
Unexpected input(s) 'script_stop'
```

`appleboy/ssh-action` v1.2 에서 없어진 입력이라 조용히 무시되고 있었다.
실제 입력 36개를 조회해 대체 입력이 없음을 확인하고, 스크립트 첫 줄의 `set -e` 가
같은 역할을 하므로 죽은 입력만 제거했다. `#11` 은 경고 0개.

---

## 6. 캡처 목록

### 4일차 (CI/CD)

| 파일 | 내용 | 종류 |
|---|---|---|
| `30_github_repo.png` | 레포 메인 — README, CI/CD 배지 `PASSING` | 화면 캡처 |
| `31_actions_runs.png` | Actions 실행 목록 — 성공/실패 이력 | 화면 캡처 |
| `32_actions_run.png` | 실행 상세 — job 3개 성공, 3m 13s | 화면 캡처 |
| `33_dockerhub_classifier.png` | Docker Hub 태그 — 커밋해시 + latest | 화면 캡처 |
| `34_dockerhub_frontend.png` | Docker Hub 태그 (프론트) | 화면 캡처 |
| `35_cmd_verify.png` | 검증 명령어 출력 | **텍스트를 이미지로 렌더** |
| `20_deployed_model_info.png` | 배포된 VM 의 `/model-info` (`trained_at` 확인) | 화면 캡처 |
| `21_deployed_streamlit.png` | 배포된 VM 의 Streamlit | 화면 캡처 |
| `22_actions_run.png` | 실행 상세 (README 삽입용) | 화면 캡처 |

### 로컬 검증 (새 이미지)

| 파일 | 내용 |
|---|---|
| `10_swagger_docs_v2.png` | Swagger — 엔드포인트 4개, API v1.1.0 |
| `11_swagger_predict_v2.png` | `POST /predict` — 확률 분포 포함 |
| `12_swagger_model_info.png` | `GET /model-info` |
| `13_streamlit_v2.png` | Streamlit 예측 결과 |

### 3일차 (수동 배포, 참고용)

`01`~`09` — 3일차 기록. 자세한 내용은 [`../docs/DAY3.md`](../docs/DAY3.md).

35 번은 터미널 화면을 그대로 찍은 것이 아니라, 이 문서 3·5절의 실제 출력 텍스트를
읽기 좋게 렌더링한 것이다. 원문은 이 문서에 그대로 실려 있다.

---

## 7. 재현 방법

```bash
# 배포된 서비스 캡처 (VM 이 켜져 있어야 함)
python captures/capture_deployed.py <VM_IP> <ACTIONS_RUN_URL>

# 제출용 캡처 (레포·Actions·Docker Hub — VM 불필요)
python captures/capture_day4.py

# 로컬 이미지로 API 화면 캡처 (컨테이너를 띄운 뒤)
python captures/capture_v2.py
```

---

## 8. 정리 상태

```
$ gcloud compute instances list
iris-vm  us-central1-a  e2-micro  10.128.0.2  (외부 IP 없음)  TERMINATED

$ gcloud compute addresses list
Listed 0 items.
```

- VM **중지** — CPU·외부 IP 과금 정지
- 예약 IP 0개 — 숨은 과금 없음
- 디스크 30GB `pd-standard` 보존 (us-central1 무료 등급 내)

다시 켤 때는 외부 IP 가 바뀌므로 `bash scripts/update-vm-host.sh` 로
`GCP_VM_HOST` 시크릿을 갱신한 뒤 푸시하면 자동 배포가 다시 붙는다.
