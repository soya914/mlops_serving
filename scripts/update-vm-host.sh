#!/usr/bin/env bash
# VM 을 start 하면 임시 외부 IP 가 바뀐다.
# 바뀐 IP 를 GitHub 시크릿 GCP_VM_HOST 에 다시 넣어주는 스크립트.
#
#   bash scripts/update-vm-host.sh
#
set -euo pipefail

ZONE="${ZONE:-us-central1-a}"
VM="${VM:-iris-vm}"

STATUS=$(gcloud compute instances describe "$VM" --zone="$ZONE" --format="get(status)")
if [ "$STATUS" != "RUNNING" ]; then
  echo "VM 이 $STATUS 상태입니다. 먼저 켜세요:"
  echo "  gcloud compute instances start $VM --zone=$ZONE"
  exit 1
fi

IP=$(gcloud compute instances describe "$VM" --zone="$ZONE" \
  --format="get(networkInterfaces[0].accessConfigs[0].natIP)")

echo "현재 외부 IP: $IP"
printf '%s' "$IP" | gh secret set GCP_VM_HOST
echo "GCP_VM_HOST 갱신 완료. 이제 빈 커밋으로 파이프라인을 돌리면 됩니다:"
echo "  git commit --allow-empty -m 'redeploy' && git push"
