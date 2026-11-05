"""用 Playwright 與本機 Chromium 驗證分頁、鍵盤操作、計數及手機版。"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    parser.add_argument("--screenshots", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "docs/progress.json").read_text(encoding="utf-8"))
    checks = [check for stage in data["milestones"] for check in stage["checks"]]
    check_count = f"{sum(check['done'] for check in checks)} / {len(checks)}"
    stages_done = sum(all(check["done"] for check in stage["checks"]) for stage in data["milestones"])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, headless=True)
        try:
            page = browser.new_page(viewport={"width": 1280, "height": 1000})
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            # 直接載入本機 HTML 內容；此離線頁不需要 HTTP 伺服器或 file URL 導覽。
            page.set_content((root / "docs/progress.html").read_text(encoding="utf-8"))
            assert page.locator("#milestones article").count() == 6
            assert page.locator("#check-count").inner_text() == check_count
            assert page.locator("#stage-count").inner_text() == f"{stages_done} / 6"
            if args.screenshots:
                args.screenshots.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(args.screenshots / "milestones.png"), full_page=True)
            page.get_by_role("tab", name="模組化架構").click()
            assert page.locator("#module-panel").is_visible()
            assert page.locator("#modules article").count() == 11
            page.locator("#filter").select_option("verified")
            assert page.locator("#modules article").count() == 1
            assert "設定儲存" in page.locator("#modules").inner_text()
            page.locator("#filter").select_option("all")
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / "modules.png"), full_page=True)
            page.get_by_role("tab", name="模組化架構").focus()
            page.keyboard.press("ArrowLeft")
            assert page.locator("#milestone-panel").is_visible()
            if data.get('component_rollout'):
                rollout=data['component_rollout']
                component_checks=[check for phase in rollout['phases'] for check in phase['checks']]
                page.get_by_role('tab',name='元件導入規劃').click()
                assert page.locator('#component-panel').is_visible()
                assert page.locator('#component-count').inner_text()==f"{sum(check['done'] for check in component_checks)} / {len(component_checks)}"
                assert page.locator('#component-phases article').count()==len(rollout['phases'])
                assert page.locator('#component-phases details').count()==len(component_checks)
                assert page.locator('#component-modules article').count()==len(rollout['modules'])
                first=page.locator('#component-phases details').first
                first.locator('summary').click()
                assert first.locator('p').is_visible()
                if args.screenshots:
                    page.screenshot(path=str(args.screenshots/'components.png'),full_page=True)
                page.get_by_role('tab',name='元件導入規劃').focus()
                page.keyboard.press('ArrowRight')
                assert page.locator('#milestone-panel').is_visible()
                page.keyboard.press('End')
                assert page.locator('#component-panel').is_visible()
                page.set_viewport_size({'width':390,'height':844})
                assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                if args.screenshots:
                    page.screenshot(path=str(args.screenshots/'components-mobile.png'),full_page=True)
                page.get_by_role('tab',name='里程碑進度').click()
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
            if args.screenshots:
                page.screenshot(path=str(args.screenshots / "mobile.png"), full_page=True)
            assert not errors, errors
        finally:
            browser.close()
    print("Browser checks passed: baseline milestones, modules, component rollout, filters, keyboard, mobile, JavaScript errors")


if __name__ == "__main__":
    main()
