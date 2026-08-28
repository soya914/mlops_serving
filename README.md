<div align="center">

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/banner-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="docs/assets/banner-light.svg">
  <img src="docs/assets/banner-light.svg" alt="Iris Classifier — 붓꽃 분류 모델 서빙 · CI/CD 자동화 파이프라인" width="100%">
</picture>

<br><br>

[![CI/CD](https://img.shields.io/github/actions/workflow/status/soya914/mlops_serving/main.yml?branch=main&style=for-the-badge&logo=githubactions&logoColor=white&label=CI%2FCD)](https://github.com/soya914/mlops_serving/actions/workflows/main.yml)
[![Docker Image](https://img.shields.io/docker/v/soya14/iris-classifier?style=for-the-badge&logo=docker&logoColor=white&label=image&color=2496ED)](https://hub.docker.com/r/soya14/iris-classifier)
[![Last Commit](https://img.shields.io/github/last-commit/soya914/mlops_serving?style=for-the-badge&logo=git&logoColor=white&color=F05032)](https://github.com/soya914/mlops_serving/commits/main)
[![Top Language](https://img.shields.io/github/languages/top/soya914/mlops_serving?style=for-the-badge&logo=python&logoColor=white&color=8957e5)](https://github.com/soya914/mlops_serving)

![Python](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge&logo=scikitlearn&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)
![GCP](https://img.shields.io/badge/Google_Cloud-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)

### `git push` 한 번이면 — 학습부터 GCP 배포, 응답 확인까지 사람 손이 닿지 않습니다

<img src="docs/assets/divider.svg" width="100%" alt="">

</div>

## ⚡ 파이프라인

```mermaid
flowchart LR
    A(["🚀 git push"]) --> B["🧠 모델 학습<br/><code>train.py</code>"]
    B --> C{"🧪 테스트<br/>API 응답 + 정확도 ≥ 0.95"}
    C -- "실패" --> X(["🛑 중단<br/>빌드조차 안 함"])
    C -- "통과" --> D["📦 이미지 2개 빌드"]
    D --> E["🐳 Docker Hub 푸시<br/><code>:latest</code> + <code>:커밋해시</code>"]
    E --> F["☁️ GCP VM SSH 배포<br/>컨테이너 교체"]
    F --> G{"❤️ /health 응답?"}
    G -- "무응답 60초" --> Y(["🛑 실패 처리"])
    G -- "정상" --> Z(["✅ 배포 완료"])

    style A fill:#8957e5,stroke:#6e40c9,color:#fff
    style X fill:#ffdcd7,stroke:#cf222e,color:#82071e
    style Y fill:#ffdcd7,stroke:#cf222e,color:#82071e
    style Z fill:#d3f5d8,stroke:#1a7f37,color:#0a3a1a
    style C fill:#fff8c5,stroke:#9a6700,color:#4d2d00
    style G fill:#fff8c5,stroke:#9a6700,color:#4d2d00
```

> **핵심은 "깨지면 앞에서 멈춘다"입니다.**
> 정확도가 떨어진 모델도, 빌드가 깨진 이미지도 운영 서버까지 흘러가지 못합니다.

| 단계 | Job | 하는 일 | 실패하면 |
|:--:|:---|:---|:---|
| 1️⃣ | `train-and-test` | 모델 학습 → API 응답 테스트 → 정확도 게이트 | 빌드 안 함 |
| 2️⃣ | `build-and-push` | 이미지 2개 빌드 → Docker Hub 푸시 | 배포 안 함 |
| 3️⃣ | `deploy` | VM SSH → pull → 컨테이너 교체 → `/health` 확인 | 워크플로 🔴 |

학습된 `model.joblib` 은 artifact 로 다음 job 에 전달됩니다.
따라서 **배포된 이미지 속 모델 = 방금 테스트를 통과한 바로 그 모델** 입니다.

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 📸 미리보기

<table>
  <tr>
    <td width="50%" align="center">
      <img src="captures/03_streamlit_before.png" alt="Streamlit 입력 화면" width="100%"><br>
      <sub><b>🎛️ Streamlit — 슬라이더로 꽃 치수 입력</b></sub>
    </td>
    <td width="50%" align="center">
      <img src="captures/04_streamlit_result.png" alt="Streamlit 예측 결과" width="100%"><br>
      <sub><b>🌸 예측 결과</b></sub>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center">
      <img src="captures/01_swagger_docs.png" alt="Swagger UI" width="100%"><br>
      <sub><b>📘 FastAPI Swagger 문서</b></sub>
    </td>
    <td width="50%" align="center">
      <img src="captures/02_swagger_predict_result.png" alt="POST /predict 응답" width="100%"><br>
      <sub><b>⚡ POST /predict 200 OK</b></sub>
    </td>
  </tr>
</table>

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 🏗️ 아키텍처

무료 등급 e2-micro **한 대** 안에서 컨테이너 두 개가 돕니다. 인스턴스를 늘리면 무료 등급을 벗어나기 때문입니다.

```mermaid
flowchart TB
    U(["👤 사용자"])

    subgraph GCP["☁️ GCP VM · e2-micro · us-central1"]
        direction TB
        F["🎛️ <b>iris-front</b><br/>Streamlit<br/><code>:8501</code>"]
        B["⚙️ <b>iris-api</b><br/>FastAPI + model.joblib<br/><code>:80 → :8000</code>"]
        F -- "http://172.17.0.1/predict<br/>도커 브리지 게이트웨이" --> B
    end

    U -- "웹 UI" --> F
    U -- "Swagger / curl" --> B

    style GCP fill:#f6f2ff,stroke:#8957e5,stroke-width:2px
    style F fill:#ffe4e6,stroke:#e11d48,color:#881337
    style B fill:#d1fae5,stroke:#059669,color:#064e3b
    style U fill:#e0e7ff,stroke:#4f46e5,color:#1e1b4b
```

프론트엔드는 백엔드를 **외부 IP가 아니라 도커 브리지 게이트웨이**로 호출합니다.
VM을 껐다 켜서 외부 IP가 바뀌어도 내부 통신은 그대로 살아 있습니다.

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 🔌 API

베이스 URL: `http://<VM 외부 IP>` — ⚠️ **`https` 아닙니다**

| | 메서드 | 경로 | 설명 |
|:--:|:---|:---|:---|
| 🏠 | `GET` | `/` | 서버 생존 메시지 |
| ❤️ | `GET` | `/health` | `{"status": "ok"}` — CD 검증에 사용 |
| 📘 | `GET` | `/docs` | Swagger UI |
| 🔮 | `POST` | `/predict` | 붓꽃 품종 예측 |

```bash
curl -X POST http://<VM IP>/predict \
  -H "Content-Type: application/json" \
  -d '{"data":[6.7,3.0,5.2,2.3]}'
```

```json
{ "class_index": 2, "class_name": "virginica" }
```

<details>
<summary><b>📥 요청 형식과 예측 예시 펼쳐보기</b></summary>

<br>

`data` 는 실수 4개이며 순서가 정해져 있습니다.

| 순서 | 항목 | 단위 |
|:--:|:---|:---|
| 0 | 꽃받침 길이 (sepal length) | cm |
| 1 | 꽃받침 너비 (sepal width) | cm |
| 2 | 꽃잎 길이 (petal length) | cm |
| 3 | 꽃잎 너비 (petal width) | cm |

| 입력 | 응답 | 품종 |
|:---|:---|:---|
| `[5.1, 3.5, 1.4, 0.2]` | `{"class_index": 0, "class_name": "setosa"}` | 🌱 setosa |
| `[6.0, 2.7, 5.1, 1.6]` | `{"class_index": 1, "class_name": "versicolor"}` | 🌿 versicolor |
| `[6.7, 3.0, 5.2, 2.3]` | `{"class_index": 2, "class_name": "virginica"}` | 🌷 virginica |

</details>

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 🚀 로컬에서 돌려보기

```bash
pip install -r requirements.txt -r requirements-dev.txt
python train.py      # model.joblib 생성
pytest               # 테스트 5개
uvicorn main:app --reload
```

브라우저에서 `http://127.0.0.1:8000/docs` 로 접속하면 Swagger UI가 뜹니다.

<details>
<summary><b>🐳 도커로 띄우기</b></summary>

<br>

```bash
docker build -t iris-classifier .
docker run -d -p 8000:8000 iris-classifier
```

프론트엔드까지 같이 띄우려면:

```bash
docker build -f Dockerfile.frontend -t iris-frontend .
docker run -d -p 8501:8501 -e API_URL=http://host.docker.internal:8000/predict iris-frontend
```

</details>

<details>
<summary><b>🧪 테스트가 무엇을 막아주나</b></summary>

<br>

`tests/test_api.py` 는 5개입니다.

| 테스트 | 막아주는 사고 |
|:---|:---|
| `test_root`, `test_health` | 서버가 아예 안 뜨는 이미지 배포 |
| `test_predict_setosa` | 응답 스키마가 바뀌어 프론트가 깨지는 것 |
| `test_predict_virginica` | 클래스 매핑이 뒤섞이는 것 |
| `test_model_accuracy` | **정확도 0.95 미만 모델의 배포** |

</details>

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 🔐 필요한 시크릿 5개

`Settings → Secrets and variables → Actions`

| | 이름 | 값 |
|:--:|:---|:---|
| 🐳 | `DOCKERHUB_USERNAME` | Docker Hub 아이디 |
| 🔑 | `DOCKERHUB_TOKEN` | Docker Hub 액세스 토큰 — **Read & Write** |
| 🌐 | `GCP_VM_HOST` | VM 외부 IP |
| 👤 | `GCP_VM_USERNAME` | VM SSH 계정명 |
| 🗝️ | `GCP_SSH_KEY` | 배포용 SSH 개인키 전문 |

> [!WARNING]
> **VM을 껐다 켜면 외부 IP가 바뀝니다.** `GCP_VM_HOST` 가 옛날 IP를 가리키면 배포가 타임아웃으로 죽습니다.
> ```bash
> bash scripts/update-vm-host.sh
> ```
> 이 한 줄이 현재 IP를 읽어 시크릿을 갱신해 줍니다.

> [!CAUTION]
> `GCP_SSH_KEY` 는 서버 접속 권한 그 자체입니다. 채팅·문서·커밋 어디에도 남기지 마세요.
> `.gitignore` 에 `gcp_deploy_key*` 를 넣어 두었지만, 애초에 레포 폴더 밖에서 만드는 것이 안전합니다.

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 🗺️ 프로젝트 여정

```mermaid
flowchart LR
    D1["📓 1~2일차<br/>모델 학습<br/><sub>scikit-learn</sub>"]
    D2["🔌 3일차 前<br/>FastAPI 서빙<br/><sub>로컬</sub>"]
    D3["☁️ 3일차<br/>GCP VM 수동 배포<br/><sub>손으로 pull &amp; run</sub>"]
    D4["🤖 4일차<br/>CI/CD 자동화<br/><sub>push 한 번</sub>"]

    D1 --> D2 --> D3 --> D4

    style D1 fill:#e0e7ff,stroke:#4f46e5,color:#1e1b4b
    style D2 fill:#d1fae5,stroke:#059669,color:#064e3b
    style D3 fill:#fef3c7,stroke:#d97706,color:#78350f
    style D4 fill:#f3e8ff,stroke:#9333ea,color:#4c1d95
```

3일차까지는 이미지를 만들고 VM에 들어가 `pull` 하고 `run` 하는 일을 **매번 손으로** 했습니다.
모델이 바뀔 때마다 반복되던 그 과정을 4일차에 전부 자동화했습니다.

<div align="center"><img src="docs/assets/divider.svg" width="100%" alt=""></div>

## 📁 폴더 구조

```
mlops_serving/
├── 🤖 .github/workflows/main.yml   CI/CD 파이프라인 (3 jobs)
├── ⚙️  main.py                      FastAPI 서버
├── 🧠 train.py                     모델 학습
├── 🎛️  streamlit_app.py             프론트엔드
├── 💾 model.joblib                 학습된 모델 (CI가 매번 새로 생성)
├── 🐳 Dockerfile                   백엔드 이미지
├── 🐳 Dockerfile.frontend          프론트 이미지
├── 🧪 tests/test_api.py            API 응답 + 정확도 게이트
├── ⚙️  pytest.ini                   import 경로 고정
├── 🔧 scripts/update-vm-host.sh    VM IP 변경 시 시크릿 갱신
├── 📚 docs/
│   ├── DAY3.md                    GCP 수동 배포 기록 · 요금 관리
│   └── DAY4.md                    CI/CD 구축 · 트러블슈팅
└── 📸 captures/                    실행 결과 캡처
```

## 📚 문서

<table>
  <tr>
    <td width="50%">
      <h3>🤖 <a href="docs/DAY4.md">DAY4 — CI/CD 구축</a></h3>
      시크릿 설정, 강의 자료대로 하면 깨지는 지점 4가지, 실패 증상별 원인표
    </td>
    <td width="50%">
      <h3>☁️ <a href="docs/DAY3.md">DAY3 — GCP 수동 배포</a></h3>
      VM 생성, 방화벽, 컨테이너 2개 구성, 요금 관리와 재시작 절차
    </td>
  </tr>
</table>

## 🐳 이미지

| 이미지 | 역할 | 포트 |
|:---|:---|:---|
| [`soya14/iris-classifier`](https://hub.docker.com/r/soya14/iris-classifier) | FastAPI + 모델 | `80 → 8000` |
| [`soya14/iris-frontend`](https://hub.docker.com/r/soya14/iris-frontend) | Streamlit UI | `8501 → 8501` |

<br>

<div align="center">

<img src="docs/assets/divider.svg" width="100%" alt="">

<sub>🌸 Iris 데이터셋 · RandomForestClassifier · scikit-learn</sub>

</div>
