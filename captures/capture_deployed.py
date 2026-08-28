"""CI/CD 로 실제 배포된 결과를 캡처한다.

  python captures/capture_deployed.py <VM_IP> <ACTIONS_RUN_URL>

- GCP VM 에 떠 있는 API 와 Streamlit
- GitHub Actions 실행 결과 (job 3개)
"""
import sys
import time

from playwright.sync_api import sync_playwright

IP = sys.argv[1] if len(sys.argv) > 1 else "136.65.26.42"
RUN_URL = sys.argv[2] if len(sys.argv) > 2 else ""
OUT = "captures"

ok, fail = [], []


def shot(target, path):
    target.screenshot(path=f"{OUT}/{path}")
    ok.append(path)


def expand(page, path):
    block = page.locator("div.opblock").filter(
        has=page.locator(".opblock-summary-path", has_text=path)
    ).first
    block.scroll_into_view_if_needed()
    block.locator(".opblock-summary").click()
    page.wait_for_timeout(700)
    return block


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=2)

    # 20. 배포된 API 의 /model-info — 학습 시각이 CI 실행 시각과 같다
    try:
        page.goto(f"http://{IP}/docs", wait_until="networkidle", timeout=60000)
        page.wait_for_selector(".opblock", timeout=30000)
        block = expand(page, "/model-info")
        block.get_by_role("button", name="Try it out").click()
        page.wait_for_timeout(300)
        block.get_by_role("button", name="Execute").click()
        block.locator(".live-responses-table").wait_for(timeout=20000)
        page.wait_for_timeout(1000)
        shot(block, "20_deployed_model_info.png")
    except Exception as e:
        fail.append(f"20: {type(e).__name__} {e}")

    # 21. 배포된 Streamlit
    try:
        page.goto(f"http://{IP}:8501", wait_until="networkidle", timeout=60000)
        page.wait_for_selector("text=붓꽃 분류기", timeout=40000)
        time.sleep(2.5)
        page.get_by_role("button", name="예측하기").click()
        time.sleep(3.0)
        shot(page, "21_deployed_streamlit.png")
    except Exception as e:
        fail.append(f"21: {type(e).__name__} {e}")

    # 22. GitHub Actions 실행 결과
    if RUN_URL:
        try:
            p2 = browser.new_page(viewport={"width": 1440, "height": 1000}, device_scale_factor=2)
            p2.goto(RUN_URL, wait_until="networkidle", timeout=60000)
            p2.wait_for_timeout(4000)
            shot(p2, "22_actions_run.png")
            p2.close()
        except Exception as e:
            fail.append(f"22: {type(e).__name__} {e}")

    browser.close()

print("성공:", ", ".join(ok) if ok else "없음")
print("실패:", "; ".join(fail) if fail else "없음")
sys.exit(1 if fail else 0)
