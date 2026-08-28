"""Docker Hub 페이지 캡처 + 실제 명령어 출력의 터미널 렌더링."""
import html
import pathlib
import time

from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).parent
ok, fail = [], []


def read(name):
    p = HERE / name
    return p.read_text(encoding="utf-8", errors="replace").strip() if p.exists() else ""


TERMINAL_CSS = """
body { margin:0; background:#0d1117; font-family:'D2Coding','Consolas','Courier New',monospace; }
.win { margin:0; padding:0; }
.bar { background:#21262d; padding:10px 16px; display:flex; align-items:center; gap:8px;
       border-bottom:1px solid #30363d; }
.dot { width:12px; height:12px; border-radius:50%; }
.title { color:#8b949e; font-size:13px; margin-left:10px; }
pre { color:#c9d1d9; font-size:14px; line-height:1.6; padding:18px 20px; margin:0;
      white-space:pre; }
.p { color:#7ee787; }
"""


def render(page, title, body, out):
    lines = []
    for ln in body.split("\n"):
        e = html.escape(ln)
        lines.append(f'<span class="p">{e}</span>' if ln.startswith("$ ") else e)
    doc = f"""<html><head><meta charset="utf-8"><style>{TERMINAL_CSS}</style></head>
<body><div class="win">
<div class="bar">
  <div class="dot" style="background:#ff5f56"></div>
  <div class="dot" style="background:#ffbd2e"></div>
  <div class="dot" style="background:#27c93f"></div>
  <div class="title">{html.escape(title)}</div>
</div>
<pre>{"<br>".join(lines)}</pre>
</div></body></html>"""
    page.set_content(doc)
    time.sleep(0.4)
    page.locator(".win").screenshot(path=out)


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1100, "height": 700}, device_scale_factor=2)

    # ── Docker Hub 이미지 페이지 ──
    for idx, repo in enumerate(["iris-classifier", "iris-frontend"], start=5):
        out = f"{idx:02d}_dockerhub_{repo}.png"
        try:
            page.goto(f"https://hub.docker.com/r/soya14/{repo}",
                      wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(6000)
            page.screenshot(path=out)
            ok.append(out)
        except Exception as e:
            fail.append(f"{out}: {type(e).__name__} {e}")

    # ── 실제 명령어 출력 렌더링 ──
    jobs = [
        ("07_cmd_local_build.png", "로컬(WSL Ubuntu) — 빌드된 이미지", read("_local_docker.txt")),
        ("08_cmd_vm_docker.png", "GCP VM (iris-vm) — 실행 중인 컨테이너", read("_vm.txt")),
        ("09_cmd_gcloud.png", "gcloud — 인스턴스 / 방화벽 규칙", read("_gcloud.txt")),
    ]
    for out, title, body in jobs:
        if not body:
            fail.append(f"{out}: 원본 텍스트 없음")
            continue
        try:
            render(page, title, body, out)
            ok.append(out)
        except Exception as e:
            fail.append(f"{out}: {type(e).__name__} {e}")

    browser.close()

print("성공:")
for x in ok:
    print("  ", x)
if fail:
    print("실패:")
    for x in fail:
        print("  ", x)
