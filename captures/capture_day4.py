"""4일차(CI/CD) 제출용 캡처.

  python captures/capture_day4.py

찍는 것:
  30_github_repo.png       레포 메인 (README 상단 · CI/CD 배지)
  31_actions_runs.png      Actions 실행 목록
  32_actions_run.png       실행 상세 (job 3개)
  33_dockerhub_classifier.png / 34_dockerhub_frontend.png   Docker Hub 태그
  35_cmd_verify.png        검증 명령어 출력 (텍스트를 이미지로 렌더)

배포된 서비스 화면(20·21)은 VM 이 켜져 있을 때 capture_deployed.py 로 미리 찍어 둔 것.
"""
import html
import sys
import pathlib

from playwright.sync_api import sync_playwright

REPO = "soya914/mlops_serving"
RUN_URL = sys.argv[1] if len(sys.argv) > 1 else \
    "https://github.com/soya914/mlops_serving/actions/runs/33140305644"
OUT = pathlib.Path("captures")

HIDE = """
() => {
  ['#onetrust-consent-sdk','#onetrust-banner-sdk','.onetrust-pc-dark-filter',
   '[id*="cookie"]','[class*="cookie-banner"]','[data-testid="marketing-banner"]']
    .forEach(s => document.querySelectorAll(s).forEach(e => e.remove()));
  document.querySelectorAll('a').forEach(a => {
    if (a.textContent && a.textContent.includes('Insights on the state of AI agents')) {
      let p = a; for (let i = 0; i < 4 && p.parentElement; i++) p = p.parentElement;
      p.remove();
    }
  });
}
"""

# 이 세션에서 실제로 받은 출력 그대로. 새로 실행한 값이 아니라 기록이다.
TERMINAL = [
    ("배포 검증 — 서울에서 GCP VM(us-central1) 호출  ·  2026-08-28 14:05 KST", [
        ("$ curl http://136.65.26.42/health",
         '{"status":"ok"}'),
        ("$ curl http://136.65.26.42/model-info",
         '{"available":true,"best_model":"logistic_regression","cv_accuracy":0.9583,\n'
         ' "holdout_accuracy":0.9333,"sklearn_version":"1.9.0",\n'
         ' "trained_at":"2026-08-28T03:55:58+00:00"}'),
        ("$ curl -X POST http://136.65.26.42/predict -d '{\"data\":[5.1,3.5,1.4,0.2]}'",
         '{"class_index":0,"class_name":"setosa","confidence":0.9808,\n'
         ' "probabilities":{"setosa":0.9808,"versicolor":0.0192,"virginica":0.0}}'),
        ("$ curl -X POST http://136.65.26.42/predict -d '{\"data\":[6.7,3.0,5.2,2.3]}'",
         '{"class_index":2,"class_name":"virginica","confidence":0.9565,\n'
         ' "probabilities":{"setosa":0.0001,"versicolor":0.0435,"virginica":0.9565}}'),
        ("$ curl -o /dev/null -w '%{http_code}' -X POST .../predict -d '{\"data\":[6.7,3.0,5.2]}'",
         '422        # 값이 4개가 아니면 500 이 아니라 422'),
    ]),
    ("VM 안에서 — CI/CD 가 교체한 컨테이너", [
        ("$ sudo docker ps",
         'iris-front | soya14/iris-frontend:97429ba1061890...   | Up | 0.0.0.0:8501->8501/tcp\n'
         'iris-api   | soya14/iris-classifier:97429ba1061890... | Up | 0.0.0.0:80->8000/tcp'),
        ("$ sudo docker images",
         'soya14/iris-frontend:97429ba10618902182f60a451722e34821e06e23   2 minutes ago\n'
         'soya14/iris-classifier:97429ba10618902182f60a451722e34821e06e23 2 minutes ago\n'
         'soya14/iris-frontend:v1                                         25 hours ago\n'
         'soya14/iris-classifier:v1                                       25 hours ago'),
    ]),
    ("GitHub Actions 결과", [
        ("$ gh run list --limit 2",
         'success  Document the first successful end-to-end deploy; drop dead script_stop\n'
         'success  Trigger full pipeline: first run with DOCKERHUB_TOKEN in place'),
        ("$ gh secret list",
         'DOCKERHUB_TOKEN       2026-08-28T03:47:14Z\n'
         'DOCKERHUB_USERNAME    2026-08-28T02:28:26Z\n'
         'GCP_SSH_KEY           2026-08-28T02:28:29Z\n'
         'GCP_VM_HOST           2026-08-28T02:28:28Z\n'
         'GCP_VM_USERNAME       2026-08-28T02:28:27Z'),
    ]),
    ("정리 — VM 중지", [
        ("$ gcloud compute instances stop iris-vm --zone=us-central1-a",
         'Stopping instance(s) iris-vm...done.'),
        ("$ gcloud compute instances list",
         'NAME     ZONE           MACHINE_TYPE  INTERNAL_IP  EXTERNAL_IP  STATUS\n'
         'iris-vm  us-central1-a  e2-micro      10.128.0.2                TERMINATED'),
        ("$ gcloud compute addresses list",
         'Listed 0 items.        # 예약 IP 없음 — 숨은 과금 없음'),
    ]),
]


def terminal_html():
    blocks = []
    for title, pairs in TERMINAL:
        rows = []
        for cmd, out in pairs:
            rows.append(f'<div class="cmd">{html.escape(cmd)}</div>')
            rows.append(f'<div class="out">{html.escape(out)}</div>')
        blocks.append(f'<section><h2>{html.escape(title)}</h2>{"".join(rows)}</section>')
    css = (
        "*{box-sizing:border-box}"
        "body{margin:0;padding:34px;background:#0d1117;"
        "font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}"
        "h1{color:#f0f6fc;font-size:23px;margin:0 0 6px}"
        "p.sub{color:#8b949e;font-size:13px;margin:0 0 24px}"
        "section{background:#12161f;border:1px solid #262c38;border-radius:10px;"
        "padding:18px 20px;margin-bottom:16px}"
        "h2{color:#c4b5fd;font-size:14px;margin:0 0 12px;letter-spacing:.5px}"
        ".cmd{color:#7ee787;font-size:14px;margin-top:12px;white-space:pre-wrap;word-break:break-all}"
        ".out{color:#c9d1d9;font-size:13.5px;white-space:pre-wrap;margin:5px 0 0 14px;"
        "border-left:2px solid #30363d;padding-left:12px;line-height:1.6}"
    )
    return ('<!doctype html><meta charset="utf-8"><style>' + css + '</style>'
            '<h1>4일차 CI/CD — 실행 기록</h1>'
            '<p class="sub">soya914/mlops_serving · 아래는 이 프로젝트를 진행하며 실제로 받은 출력이다.</p>'
            + "".join(blocks))


ok, fail = [], []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)

    def shot(name, url, wait=4000, height=1000, width=1440, full=False, hide=False):
        try:
            page = browser.new_page(viewport={"width": width, "height": height},
                                    device_scale_factor=2)
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(wait)
            if hide:
                page.evaluate(HIDE)
                page.wait_for_timeout(600)
            page.screenshot(path=str(OUT / name), full_page=full)
            page.close()
            ok.append(name)
        except Exception as e:
            fail.append(f"{name}: {type(e).__name__} {e}")

    shot("30_github_repo.png", f"https://github.com/{REPO}", wait=5000, height=1150)
    shot("31_actions_runs.png", f"https://github.com/{REPO}/actions", wait=4500, height=900)
    shot("32_actions_run.png", RUN_URL, wait=4500, height=1000)
    shot("33_dockerhub_classifier.png",
         "https://hub.docker.com/r/soya14/iris-classifier/tags",
         wait=7000, width=1200, height=900, hide=True)
    shot("34_dockerhub_frontend.png",
         "https://hub.docker.com/r/soya14/iris-frontend/tags",
         wait=7000, width=1200, height=900, hide=True)

    # 명령어 출력 렌더
    try:
        tmp = OUT / "_terminal.html"
        tmp.write_text(terminal_html(), encoding="utf-8")
        page = browser.new_page(viewport={"width": 1100, "height": 800}, device_scale_factor=2)
        page.goto(tmp.resolve().as_uri(), wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(700)
        page.screenshot(path=str(OUT / "35_cmd_verify.png"), full_page=True)
        page.close()
        tmp.unlink()
        ok.append("35_cmd_verify.png")
    except Exception as e:
        fail.append(f"35: {type(e).__name__} {e}")

    browser.close()

print("성공:", ", ".join(ok) if ok else "없음")
print("실패:", "; ".join(fail) if fail else "없음")
sys.exit(1 if fail else 0)
