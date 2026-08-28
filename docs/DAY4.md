# 4일차 — CI/CD 구축 기록

3일차까지는 "학습 → 이미지 빌드 → Docker Hub 푸시 → VM 접속 → pull → run" 을 매번 손으로 했다.
4일차는 그것을 **`main` 에 푸시하면 알아서 굴러가게** 만든 기록이다.

```
git push
  ↓  train-and-test    후보 3개 교차검증 → 최고 모델 저장 → 테스트 14개
  ↓  build-and-push    이미지 2개 빌드 → Docker Hub (:latest, :커밋해시)
  ↓  deploy            VM SSH → 컨테이너 교체 → 내부 health → 외부 /predict
 초록불
```

---

## 1. 강의 자료 그대로 쓰면 깨지는 곳

3일차 구성에 맞춰 수정한 부분이다. 전부 `.github/workflows/main.yml` 에 반영돼 있다.

### 1-1. `file: ./dockerfile` — 소문자라서 실패

리눅스 러너는 파일명 대소문자를 구분한다. 실제 파일은 `Dockerfile` 이므로
`./dockerfile` 은 `failed to read dockerfile: no such file or directory` 로 죽는다.

```diff
- file: ./dockerfile
+ file: ./Dockerfile
```

### 1-2. 이미지가 1개가 아니라 2개

3일차에 한 VM 에 백엔드(`iris-classifier`) + 프론트(`iris-frontend`) 를 같이 올렸다.
강의 자료의 `my-ml-app` 하나만 배포하면 프론트가 옛 이미지로 남는다.
→ 빌드 · 푸시 · 배포를 모두 2개씩.

### 1-3. 컨테이너 삭제가 이름으로만 되어 있음

3일차에는 컨테이너를 `--name` 없이 띄웠다. 실제로 VM 에는 이런 이름이 붙어 있었다.

```
elated_banach            soya14/iris-frontend:v1     0.0.0.0:8501->8501/tcp
xenodochial_heyrovsky    soya14/iris-classifier:v1   0.0.0.0:80->8000/tcp
```

`docker stop my-app-container` 는 아무것도 못 지우고, 새 컨테이너는
`port is already allocated` 로 실패한다. 그래서 **이름으로 한 번, 포트로 한 번** 지운다.

```bash
sudo docker rm -f iris-api iris-front 2>/dev/null || true
for p in 80 8501; do
  cid=$(sudo docker ps -q --filter "publish=$p")
  if [ -n "$cid" ]; then sudo docker rm -f $cid; fi
done
```

### 1-4. SSH 공개키를 VM 에 등록하는 단계가 빠져 있음

자료에는 `ssh-keygen` 후 `cat gcp_deploy_key` 로 개인키를 복사하는 것까지만 있다.
**공개키를 VM 이 신뢰하도록 등록하지 않으면** Actions 가 `ssh: handshake failed` 로 죽는다.

GCP 는 메타데이터로 등록한다. 인스턴스 단위 키는 프로젝트 단위 키에 **더해져서** 동작하므로
기존 접속을 깨뜨리지 않는다.

```bash
# "사용자명:공개키" 한 줄짜리 파일을 만든 뒤
printf 'leeso:%s\n' "$(cat gcp_deploy_key.pub)" > ssh-keys-metadata.txt

gcloud compute instances add-metadata iris-vm --zone=us-central1-a \
  --metadata-from-file ssh-keys=ssh-keys-metadata.txt
```

등록 후 반드시 실제로 붙는지 먼저 확인한다. Actions 에서 처음 확인하면 디버깅이 훨씬 느리다.

```bash
ssh -i gcp_deploy_key leeso@<VM IP> "whoami; sudo docker ps"
```

---

## 2. 강의 자료에 없지만 넣은 것

### 2-1. 성능 게이트 — 그리고 처음에 잘못 만들었던 것

처음 만든 게이트는 이랬다.

```python
model = joblib.load("model.joblib")
X, y = load_iris(return_X_y=True)
assert model.score(X, y) >= 0.95      # ← 학습에 쓴 데이터로 채점
```

**이건 아무것도 막지 못한다.** `train.py` 가 전체 데이터로 학습했으므로 같은 데이터로 채점하면
RandomForest 는 거의 항상 1.0 이 나온다. 성능이 실제로 나빠져도 통과한다.

그래서 `train.py` 를 고쳤다.

- 홀드아웃 20%(30건)를 먼저 떼어 둔다 — **학습에도, 모델 선택에도 쓰지 않는다**
- 학습셋 안에서만 5-fold 교차검증으로 후보 3개를 비교한다
- 이긴 모델만 저장하고, 홀드아웃으로 마지막에 한 번 채점한다
- 결과를 `metrics.json` 에 남긴다

실제 실행 결과:

```
  random_forest_100          CV 0.9500  (±0.0312)
  random_forest_300_depth3   CV 0.9500  (±0.0312)
  logistic_regression        CV 0.9583  (±0.0264)

선택된 모델: logistic_regression
  CV 정확도      0.9583
  홀드아웃 정확도 0.9333
```

게이트 기준:

| 기준 | 값 | 의미 |
|:---|:--:|:---|
| 홀드아웃 정확도 | ≥ 0.90 | 30건 중 3건 이상 틀리면 배포 중단 |
| 교차검증 정확도 | ≥ 0.93 | 학습 단계에서의 성능 저하 감지 |

> 홀드아웃이 30건뿐이라 1건 차이가 0.033 이다. 기준을 0.95 로 잡으면
> 2건만 틀려도 떨어져서 게이트가 너무 예민해진다. 그래서 0.90 으로 뒀다.

### 2-2. 모델이 바뀌면 예측도 바뀐다

RandomForest → LogisticRegression 으로 바뀌면서 실제로 예측이 달라진 입력이 있었다.

| 입력 | 이전(RF) | 현재(LogReg) | confidence |
|:---|:---|:---|:--:|
| `[6.0, 2.7, 5.1, 1.6]` | versicolor | **virginica** | 0.5268 |

versicolor 와 virginica 사이의 유명한 경계 샘플이다. 확률이 0.53 대 0.47 로 갈린다.
문서에 적어 둔 예시가 이런 경계 샘플이면 모델을 바꿀 때마다 문서가 틀리게 되므로,
**테스트와 문서에는 확실히 갈리는 샘플을 쓰는 편이 낫다.**

### 2-3. `/model-info` — 배포된 게 정말 그 모델인지 확인

`metrics.json` 을 이미지에 함께 넣고, API 로 노출했다.

```bash
curl http://<VM IP>/model-info
```
```json
{
  "available": true,
  "best_model": "logistic_regression",
  "cv_accuracy": 0.9583,
  "holdout_accuracy": 0.9333,
  "sklearn_version": "1.9.0",
  "trained_at": "2026-08-28T02:49:51+00:00"
}
```

배포 후 "지금 VM 에 올라간 게 정말 방금 학습한 모델인가" 를 눈으로 확인할 수 있다.
`metrics.json` 이 없어도 서비스는 뜨고, 이 경우 `available: false` 를 돌려준다.

### 2-4. 입력 검증

`data` 개수를 서버가 확인하지 않으면 scikit-learn 안에서 터져 `500` 이 난다.
Pydantic 검증기로 막아 `422` 로 돌려준다.

### 2-5. 커밋 해시 태그로 배포

`:latest` 만 쓰면 VM 에서 도는 것이 어느 커밋인지 알 수 없고, 롤백 대상도 특정 못 한다.
그래서 `:latest` 와 `:<커밋해시>` 를 함께 푸시하고, **배포는 커밋해시로** 한다.

### 2-6. 배포 검증 2단계

1. **VM 내부** — `docker exec` 로 컨테이너 안에서 `/health` 확인. 실패하면 `docker logs` 를 출력하고 중단
2. **외부** — 러너에서 `curl http://<IP>/health` 와 `/predict` 확인. 60초 안에 응답 없으면 실패

내부에서 먼저 보는 이유는, 컨테이너가 죽은 것과 방화벽 문제를 구분하기 위해서다.

---

## 3. 시크릿 5개

`Settings → Secrets and variables → Actions → New repository secret`

| 이름 | 값 | 얻는 곳 |
|:---|:---|:---|
| `DOCKERHUB_USERNAME` | Docker Hub 아이디 | 프로필 |
| `DOCKERHUB_TOKEN` | `dckr_pat_...` | Account settings → Personal access tokens (**Read & Write**) |
| `GCP_VM_HOST` | VM 외부 IP | `gcloud compute instances list` |
| `GCP_VM_USERNAME` | SSH 계정명 | VM 안에서 `whoami` |
| `GCP_SSH_KEY` | 개인키 전문 | `ssh-keygen -t rsa -b 4096 -f gcp_deploy_key -N ""` |

`GCP_SSH_KEY` 는 `-----BEGIN ...` 부터 `-----END ...` 까지 **마지막 줄바꿈 포함** 전부 넣는다.
한 줄이라도 빠지면 `error parsing private key` 가 뜬다.

터미널에서 넣으면 값이 화면에 남지 않는다.

```bash
gh secret set GCP_SSH_KEY < gcp_deploy_key    # 파일에서 바로
gh secret set DOCKERHUB_TOKEN                  # 붙여넣기 (입력이 가려짐)
```

> `GCP_SSH_KEY` 는 서버 접속 권한 그 자체다. 채팅 · 문서 · 커밋 어디에도 남기지 않는다.
> `.gitignore` 에 `gcp_deploy_key*` 를 넣어 뒀지만, 애초에 레포 폴더 **밖에서** 만드는 게 안전하다.

---

## 4. ⚠️ 임시 IP — 가장 자주 물리는 곳

VM 을 `stop → start` 하면 **외부 IP 가 바뀐다.** `GCP_VM_HOST` 는 그대로라서
다음 배포가 옛 IP 로 접속을 시도하다 타임아웃으로 죽는다.

**A. 임시 IP + 갱신 스크립트 (무료)**

```bash
gcloud compute instances start iris-vm --zone=us-central1-a
bash scripts/update-vm-host.sh      # 현재 IP 를 읽어 시크릿 갱신
```

**B. 고정 IP 예약 (편하지만 유료)**

```bash
gcloud compute addresses create iris-ip --region=us-central1
gcloud compute instances delete-access-config iris-vm --zone=us-central1-a \
  --access-config-name="external-nat"
gcloud compute instances add-access-config iris-vm --zone=us-central1-a \
  --access-config-name="external-nat" --address=<예약된 IP>
```

고정 IP 는 **VM 이 꺼져 있을 때도 계속 과금된다.** 임시 IP 는 VM 이 켜져 있을 때만 과금되므로,
수업용이면 A 를 쓰고 안 쓸 땐 VM 을 끄는 쪽이 싸다.
수업이 끝나면 예약을 반드시 해제한다.

```bash
gcloud compute addresses delete iris-ip --region=us-central1
```

---

## 5. 파이프라인 돌려보기

```bash
git commit --allow-empty -m "redeploy"    # 코드 변경 없이 재실행
git push
```

또는 GitHub `Actions` 탭 → 워크플로 선택 → `Run workflow` (수동 실행을 켜 뒀다).

각 job 이 실행 페이지 상단 요약에 결과를 남긴다.

- `train-and-test` — 선택된 모델, CV/홀드아웃 정확도, 후보 3개 비교표
- `build-and-push` — 푸시된 이미지와 태그
- `deploy` — `/health`, `/predict`, `/model-info` 실제 응답

---

## 6. 실패했을 때 보는 곳

| 증상 | 원인 | 조치 |
|:---|:---|:---|
| `failed to read dockerfile` | `file:` 경로 대소문자 | `./Dockerfile` |
| `unauthorized: incorrect username or password` | 토큰이 비번이거나 Read only | Read & Write 토큰 재발급 |
| `ssh: handshake failed` | 공개키 미등록 / 계정명 오타 | `add-metadata` 후 로컬 ssh 로 먼저 확인 |
| `dial tcp ...: i/o timeout` | VM 꺼짐 또는 **IP 변경** | `update-vm-host.sh` |
| `error parsing private key` | BEGIN/END 줄·줄바꿈 누락 | `gh secret set GCP_SSH_KEY < 파일` |
| `port is already allocated` | 옛 컨테이너가 포트 점유 | 포트 필터로 제거 (1-3 참조) |
| `ModuleNotFoundError: No module named 'main'` | 로컬 `python -m pytest` 는 CWD 를 import 경로에 넣지만 CI 의 `pytest` 는 안 넣음 | `pytest.ini` 의 `pythonpath = .` |
| health check 실패 | 방화벽 `tcp:80` 또는 컨테이너 기동 실패 | `sudo docker logs iris-api` |

### `ModuleNotFoundError` 는 왜 로컬에서 안 잡혔나

```
로컬 검증:  python -m pytest   → CWD 가 sys.path 에 들어감 → 통과
CI 실행:    pytest             → 안 들어감 → ModuleNotFoundError
```

같은 테스트인데 실행 방식 하나로 결과가 갈렸다.
`pytest.ini` 에 `pythonpath = .` 를 넣어 실행 방식과 무관하게 고정했고,
로컬에서도 CI 와 똑같이 `pytest` 로 한 번 더 확인했다.
