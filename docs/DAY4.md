# 4일차 — CI/CD (GitHub Actions)

3일차까지는 "모델 학습 → 이미지 빌드 → Docker Hub 푸시 → VM 접속 → pull → run" 을
매번 손으로 했다. 4일차는 그걸 **main 에 푸시하면 알아서 돌아가게** 만든다.

```
git push
   ↓
[CI] 모델 학습 → 테스트(정확도 0.95 게이트) → 통과해야 다음
   ↓
[CI] 이미지 2개 빌드 → Docker Hub 푸시 (:latest, :커밋해시)
   ↓
[CD] GCP VM 에 SSH → pull → 컨테이너 교체
   ↓
[검증] http://<VM IP>/health 가 실제로 응답하는지 확인 (실패하면 워크플로 빨간불)
```

---

## 강의 자료 그대로 쓰면 깨지는 곳

3일차 구성에 맞춰 수정한 부분이다. `.github/workflows/main.yml` 에 반영되어 있다.

### 1. `file: ./dockerfile` — 소문자라서 실패

리눅스 러너는 대소문자를 구분한다. 실제 파일은 `Dockerfile` 이므로
`./dockerfile` 은 `failed to read dockerfile: no such file or directory` 로 죽는다.
→ **`file: ./Dockerfile`**

### 2. 이미지가 1개가 아니라 2개

3일차에서 한 VM 에 백엔드(`iris-classifier`) + 프론트(`iris-frontend`) 를 같이 올렸다.
강의 자료의 `my-ml-app` 하나만 배포하면 프론트가 옛날 이미지로 남는다.
→ 빌드·푸시·배포 모두 **2개씩**.

### 3. 컨테이너 삭제가 이름으로만 되어 있음

3일차에는 컨테이너를 `--name` 없이 띄웠다. 그래서
`docker stop my-app-container` 는 아무것도 못 지우고, 새 컨테이너는
`port is already allocated` 로 실패한다.
→ 이름으로 한 번, **포트(`--filter publish=80`)로 한 번** 지운다.

### 4. SSH 공개키를 VM 에 등록하는 단계가 빠져 있음

자료에는 `ssh-keygen` 하고 `cat gcp_deploy_key` 로 개인키를 복사하는 것까지만 있다.
**공개키를 VM 이 신뢰하도록 등록하지 않으면** Actions 가
`ssh: handshake failed` 로 죽는다. GCP 는 메타데이터로 등록한다:

```bash
gcloud compute instances add-metadata iris-vm --zone=us-central1-a \
  --metadata-from-file ssh-keys=deploy_key_metadata.txt
```

`deploy_key_metadata.txt` 의 내용은 `사용자명:공개키한줄` 형식이다.

### (추가) 강의 자료에 없는 것 — 테스트와 배포 확인

"오류가 없는지 확인" 이 CI 의 본질이라, 두 가지를 넣었다.

- `tests/test_api.py` — API 응답 + **정확도 0.95 미만이면 배포 중단**
- 배포 후 `curl /health` 재시도 20회 — 응답 없으면 워크플로 실패

---

## 필요한 시크릿 5개

`Settings → Secrets and variables → Actions → New repository secret`

| 이름 | 값 | 어디서 |
|---|---|---|
| `DOCKERHUB_USERNAME` | `soya14` | Docker Hub 아이디 |
| `DOCKERHUB_TOKEN` | `dckr_pat_...` | Docker Hub → Account settings → Personal access tokens (**Read & Write**) |
| `GCP_VM_HOST` | VM 외부 IP | `gcloud compute instances list` |
| `GCP_VM_USERNAME` | `leeso` | VM 에서 `whoami` |
| `GCP_SSH_KEY` | 개인키 **전문** | 아래 참조 |

`GCP_SSH_KEY` 는 `-----BEGIN OPENSSH PRIVATE KEY-----` 부터
`-----END OPENSSH PRIVATE KEY-----` 까지, **마지막 줄바꿈 포함** 전부 넣어야 한다.
한 줄이라도 빠지면 `error parsing private key` 가 뜬다.

> 개인키는 채팅·문서·커밋 어디에도 남기지 않는다. `.gitignore` 에
> `gcp_deploy_key*` 를 넣어 두었지만, 애초에 레포 폴더 안에서 만들지 않는 게 좋다.

---

## ⚠️ 임시 IP 문제 — 이게 제일 자주 물린다

VM 을 `stop → start` 하면 **외부 IP 가 바뀐다.** 그런데 `GCP_VM_HOST` 시크릿은
그대로라서, 다음 배포가 옛날 IP 로 접속을 시도하다 타임아웃으로 죽는다.

선택지 두 가지:

**A. 매번 시크릿 갱신 (무료)**

```bash
gcloud compute instances start iris-vm --zone=us-central1-a
bash scripts/update-vm-host.sh
```

**B. 고정 IP 예약 (편하지만 유료)**

```bash
gcloud compute addresses create iris-ip --region=us-central1
gcloud compute instances delete-access-config iris-vm --zone=us-central1-a \
  --access-config-name="external-nat"
gcloud compute instances add-access-config iris-vm --zone=us-central1-a \
  --access-config-name="external-nat" --address=<예약된 IP>
```

고정 IP 는 **VM 이 꺼져 있을 때도 계속 과금된다.** 임시 IP 는 VM 이 켜져 있을 때만
과금되므로, 수업용이면 A 를 쓰고 안 쓸 땐 VM 을 끄는 쪽이 싸다.
수업이 끝나면 예약을 반드시 해제한다: `gcloud compute addresses delete iris-ip --region=us-central1`

---

## 파이프라인 돌려보기

```bash
# 코드를 아무것도 안 바꾸고 그냥 다시 돌리고 싶을 때
git commit --allow-empty -m "retry"
git push
```

또는 GitHub `Actions` 탭 → 워크플로 선택 → `Run workflow` (수동 실행을 켜뒀다).

---

## 실패했을 때 보는 곳

| 증상 | 원인 |
|---|---|
| `failed to read dockerfile` | `file:` 경로 대소문자 |
| `unauthorized: incorrect username or password` | `DOCKERHUB_TOKEN` 이 비번이거나 권한이 Read only |
| `ssh: handshake failed` | 공개키가 VM 에 등록 안 됨 / `GCP_VM_USERNAME` 오타 |
| `dial tcp ...: i/o timeout` | VM 이 꺼져 있거나 **IP 가 바뀜** (위 ⚠️ 참조) |
| `error parsing private key` | 개인키 복사할 때 BEGIN/END 줄이나 줄바꿈 누락 |
| `port is already allocated` | 옛 컨테이너가 안 지워짐 (포트 필터로 해결) |
| health check 실패 | 방화벽 `tcp:80` 규칙 / 컨테이너가 뜨자마자 죽음 → VM 에서 `sudo docker logs iris-api` |
