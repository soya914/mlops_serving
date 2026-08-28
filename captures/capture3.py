"""Docker Hub 태그 페이지 재캡처 — 동의 배너는 클릭하지 않고 화면에서만 제외한다."""
import time

from playwright.sync_api import sync_playwright

HIDE_BANNERS = """
() => {
  const kill = [
    '#onetrust-consent-sdk', '#onetrust-banner-sdk', '.onetrust-pc-dark-filter',
    '[id*="cookie"]', '[class*="cookie-banner"]', '[data-testid="marketing-banner"]',
  ];
  kill.forEach(sel => document.querySelectorAll(sel).forEach(el => el.remove()));
  // 상단 마케팅 띠 제거
  document.querySelectorAll('a').forEach(a => {
    if (a.textContent && a.textContent.includes('Insights on the state of AI agents')) {
      let p = a; for (let i = 0; i < 4 && p.parentElement; i++) p = p.parentElement;
      p.remove();
    }
  });
}
"""

ok, fail = [], []
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=2)

    for idx, repo in enumerate(["iris-classifier", "iris-frontend"], start=5):
        out = f"{idx:02d}_dockerhub_{repo}.png"
        try:
            page.goto(f"https://hub.docker.com/r/soya14/{repo}/tags",
                      wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(7000)
            page.evaluate(HIDE_BANNERS)
            page.wait_for_timeout(800)
            page.screenshot(path=out)
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
