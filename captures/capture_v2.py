"""4일차(CI/CD) 버전의 실행 화면을 캡처한다.

3일차 캡처는 VM 의 :v1 이미지를 찍은 것이라 /model-info 나 확률 필드가 없다.
이 스크립트는 새 이미지를 로컬에 띄운 상태에서 찍는다.

    docker run -d -p 8000:8000 ...        # 백엔드
    docker run -d -p 8501:8501 ...        # 프론트
    python captures/capture_v2.py
"""
import sys
import time

from playwright.sync_api import sync_playwright

API = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
UI = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8501"
OUT = "captures"

ok, fail = [], []


def shot(page, path, target=None):
    (target or page).screenshot(path=f"{OUT}/{path}")
    ok.append(path)


def expand(page, path):
    """Swagger UI 에서 해당 경로의 오퍼레이션 블록을 펼치고 그 요소를 돌려준다."""
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

    # 10. Swagger 문서 전체 — 엔드포인트 5개가 보인다
    try:
        page.goto(f"{API}/docs", wait_until="networkidle", timeout=60000)
        page.wait_for_selector(".opblock", timeout=30000)
        time.sleep(1.2)
        shot(page, "10_swagger_docs_v2.png")
    except Exception as e:
        fail.append(f"10: {type(e).__name__} {e}")

    # 11. POST /predict 실행 결과 — 확률 필드가 보인다
    try:
        block = expand(page, "/predict")
        block.get_by_role("button", name="Try it out").click()
        time.sleep(0.4)
        box = block.locator("textarea.body-param__text")
        box.fill('{\n  "data": [6.7, 3.0, 5.2, 2.3]\n}')
        block.get_by_role("button", name="Execute").click()
        block.locator(".live-responses-table").wait_for(timeout=20000)
        time.sleep(1.0)
        shot(page, "11_swagger_predict_v2.png", block)
        block.locator(".opblock-summary").click()  # 접기
        time.sleep(0.4)
    except Exception as e:
        fail.append(f"11: {type(e).__name__} {e}")

    # 12. GET /model-info — 배포된 모델이 무엇인지
    try:
        block = expand(page, "/model-info")
        block.get_by_role("button", name="Try it out").click()
        time.sleep(0.3)
        block.get_by_role("button", name="Execute").click()
        block.locator(".live-responses-table").wait_for(timeout=20000)
        time.sleep(1.0)
        shot(page, "12_swagger_model_info.png", block)
    except Exception as e:
        fail.append(f"12: {type(e).__name__} {e}")

    # 13. Streamlit 예측 결과
    try:
        page.goto(UI, wait_until="networkidle", timeout=60000)
        page.wait_for_selector("text=붓꽃 분류기", timeout=40000)
        time.sleep(2.5)
        btn = page.get_by_role("button", name="예측하기")
        btn.click()
        time.sleep(3.0)
        shot(page, "13_streamlit_v2.png")
    except Exception as e:
        fail.append(f"13: {type(e).__name__} {e}")

    browser.close()

print("성공:", ", ".join(ok) if ok else "없음")
print("실패:", "; ".join(fail) if fail else "없음")
sys.exit(1 if fail else 0)
