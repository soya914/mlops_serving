# 3일차 - GCP 외부 배포

## 이미지

- Docker Hub: `soya14/iris-classifier:v1` (public, linux/amd64)
- digest: `sha256:05e2b82ac138...`

## 로컬 환경 주의

이 PC의 **Docker Desktop은 고장 상태**(삭제 불가 소켓 파일). 도커는 WSL Ubuntu 안의 엔진을 쓴다.

```
wsl -d Ubuntu -u root -- /usr/bin/docker <명령>
```

`docker`만 치면 고장난 Docker Desktop CLI가 잡히므로 **`/usr/bin/docker`** 경로를 붙일 것.

## 재빌드 / 재푸시

```
wsl -d Ubuntu -u root -- sh -c "cd '/mnt/c/Users/leeso/클로드자동화/mlops-day3' && /usr/bin/docker build -t soya14/iris-classifier:v1 . && /usr/bin/docker push soya14/iris-classifier:v1"
```

## GCP VM 설정 (Windows 빌드 기준)

| 항목 | 값 |
|---|---|
| 머신 유형 | e2-micro |
| 리전 | us-central1 (아이오와) — 무료 대상 |
| 아키텍처 | **x86/64** |
| 디스크 | 표준 영구 디스크 |
| 스냅샷 | **백업 없음** (요금 방지) |

## VM 안에서 실행

```
sudo apt-get update
sudo apt-get install -y docker.io
sudo systemctl enable --now docker
sudo docker pull soya14/iris-classifier:v1
sudo docker run -d -p 80:8000 soya14/iris-classifier:v1
sudo docker ps
```

접속: `http://<외부IP>/docs`  ← **https 아님**

## API

| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/` | - | `{"message": "..."}` |
| GET | `/health` | - | `{"status":"ok"}` |
| POST | `/predict` | `{"data":[5.1,3.5,1.4,0.2]}` | `{"class_index":0,"class_name":"setosa"}` |

## 프론트엔드

`streamlit_app.py` 의 `API_URL` 을 VM 외부 IP로 바꾼 뒤:

```
streamlit run streamlit_app.py
```

## 4일차 끝나면

- VM **중지 및 삭제**
- 스냅샷 일정 전부 삭제
- 유료 계정 활성화했다면 **비활성화**

---

## 실제 배포 결과 (2026-08-27)

| 항목 | 값 |
|---|---|
| 프로젝트 | `bold-guru-501604-b2` |
| 인스턴스 | `iris-vm` / us-central1-a / e2-micro |
| 외부 IP | `34.44.197.207` |
| API 문서 | http://34.44.197.207/docs |
| 스트림릿 | http://34.44.197.207:8501 |
| 방화벽 | `default-allow-http` (tcp:80), `allow-streamlit-8501` (tcp:8501) — 둘 다 tag `http-server` |
| swap | 1GB (`/swapfile`, fstab 등록됨) |

### 컨테이너 2개 구성

한 VM에 백엔드·프론트엔드를 같이 올렸다. 인스턴스를 늘리면 무료 등급(e2-micro 1대)을 벗어나므로.

| 이미지 | 포트 | 역할 |
|---|---|---|
| `soya14/iris-classifier:v1` | 80 → 8000 | FastAPI + 모델 |
| `soya14/iris-frontend:v1` | 8501 → 8501 | 스트림릿 UI |

프론트엔드는 `API_URL` 환경변수로 백엔드를 찾는다. 같은 VM 안이라 도커 브리지 게이트웨이
`http://172.17.0.1/predict` 를 쓴다 — 외부 IP로 나갔다 오지 않아 IP가 바뀌어도 안 깨진다.

```
sudo docker run -d -p 8501:8501 -e API_URL=http://172.17.0.1/predict soya14/iris-frontend:v1
```

### 관리 명령어

```
gcloud compute instances stop iris-vm --zone=us-central1-a      # 중지
gcloud compute instances start iris-vm --zone=us-central1-a     # 재시작 (외부 IP 바뀜)
gcloud compute instances delete iris-vm --zone=us-central1-a    # 삭제
```

### 다시 켤 때

두 컨테이너 모두 `--restart unless-stopped` 가 걸려 있고 docker 도 부팅 시 자동 시작이라,
**VM 만 켜면 서비스가 알아서 올라온다.** (재부팅 테스트로 검증 완료)

```
gcloud compute instances start iris-vm --zone=us-central1-a
gcloud compute instances describe iris-vm --zone=us-central1-a --format="get(networkInterfaces[0].accessConfigs[0].natIP)"
```

두 번째 명령으로 **새 외부 IP** 를 확인한다. 중지하면 임시 IP 가 반납되므로 켤 때마다 바뀐다.
스트림릿은 백엔드를 내부 주소(`172.17.0.1`)로 부르기 때문에 IP 가 바뀌어도 안 깨진다.
로컬에서 `streamlit_app.py` 를 돌릴 때만 `API_URL` 을 새 IP 로 바꾸면 된다.

수동으로 다시 띄워야 한다면:

```
gcloud compute ssh iris-vm --zone=us-central1-a --command="sudo docker run -d -p 80:8000 soya14/iris-classifier:v1; sudo docker run -d -p 8501:8501 -e API_URL=http://172.17.0.1/predict soya14/iris-frontend:v1"
```

### 프론트엔드 재빌드

```
wsl -d Ubuntu -u root -- sh -c "cd '/mnt/c/Users/leeso/클로드자동화/mlops-day3' && /usr/bin/docker build -f Dockerfile.frontend -t soya14/iris-frontend:v1 . && /usr/bin/docker push soya14/iris-frontend:v1"
```

## 요금

- **VM 본체**: `us-central1` e2-micro 1대 + 표준 디스크 30GB 까지 Always Free. 지금 구성이 그 안에 있다.
- **외부 IPv4**: 2024-02 부터 과금 대상. 무료 제공량이 계정당 월 1시간뿐이라 사실상 전액 과금.
  단 **임시 IP 는 VM 이 running 일 때만** 과금된다. 중지하면 IP 가 반납되면서 요금도 멈춘다.
- 인스턴스를 하나 더 만들면 두 번째부터 정가 과금(대략 월 $6~7 + IP).

**따라서 안 쓸 땐 `stop`.** 디스크는 무료 등급 안이라 그대로 보존된다.
수업이 완전히 끝나면 `delete`.

### 현재 상태 (2026-08-27)

`iris-vm` **중지됨(TERMINATED)** — 외부 IP 반납, 과금 멈춤. 디스크와 이미지는 보존.
