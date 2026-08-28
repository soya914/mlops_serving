"""배포된 붓꽃 프로젝트의 실행 결과를 캡처한다."""
import json
import sys
import time

from playwright.sync_api import sync_playwright

IP = sys.argv[1] if len(sys.argv) > 1 else "34.10.33.109"
EXE = None  # 기본 설치본 사용

ok, fail = [], []

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=2)

    # 1. Swagger 문서
    try:
        page.goto(f"http://{IP}/docs", wait_until="networkidle", timeout=60000)
        page.wait_for_selector(".opblock", timeout=30000)
        time.sleep(1.5)
        page.screenshot(path="01_swagger_docs.png", full_page=True)
        ok.append("01_swagger_docs.png")
    except Exception as e:
        fail.append(f"01: {type(e).__name__} {e}")

    # 2. Swagger 에서 POST /predict 실제 실행
    try:
        page.locator(".opblock-post .opblock-summary").first.click(timeout=15000)
        time.sleep(1)
        page.locator("button.try-out__btn").first.click(timeout=15000)
        time.sleep(0.5)
        page.locator("textarea.body-param__text").first.fill(
            json.dumps({"data": [6.7, 3.0, 5.2, 2.3]})
        )
        page.locator("button.execute").first.click(timeout=15000)
        page.wait_for_selector(".response-col_status", timeout=30000)
        time.sleep(2)
        page.screenshot(path="02_swagger_predict_result.png", full_page=True)
        ok.append("02_swagger_predict_result.png")
    except Exception as e:
        fail.append(f"02: {type(e).__name__} {e}")

    # 3~4. 스트림릿 UI 와 예측 실행
    try:
        page.goto(f"http://{IP}:8501", wait_until="networkidle", timeout=60000)
        page.wait_for_selector("text=붓꽃 분류기", timeout=40000)
        time.sleep(2.5)
        page.screenshot(path="03_streamlit_before.png")
        ok.append("03_streamlit_before.png")

        page.get_by_text("예측하기").first.click(timeout=15000)
        page.wait_for_selector("text=예측된 클래스 번호", timeout=30000)
        time.sleep(1.5)
        page.screenshot(path="04_streamlit_result.png")
        ok.append("04_streamlit_result.png")
    except Exception as e:
        fail.append(f"03/04: {type(e).__name__} {e}")

    browser.close()

print("성공:")
for x in ok:
    print("  ", x)
if fail:
    print("실패:")
    for x in fail:
        print("  ", x)
