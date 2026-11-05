"""以本機瀏覽器檢查隨包授權目錄的搜尋、篩選及文件連結。"""
import argparse
import json
from pathlib import Path
from urllib.parse import unquote
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('--chromium',default='/usr/bin/chromium')
parser.add_argument('--screenshot',type=Path)
args=parser.parse_args()
root=Path(__file__).resolve().parents[1]/'src/desktop_app/data/licenses'
count=json.loads((root/'windows/inventory.json').read_text())['package_count']
with sync_playwright() as playwright:
    browser=playwright.chromium.launch(executable_path=args.chromium,headless=True)
    try:
        page=browser.new_page(viewport={'width':1280,'height':1000})
        errors=[];page.on('pageerror',lambda error:errors.append(str(error)))
        page.set_content((root/'index.html').read_text(encoding='utf-8'))
        assert page.locator('tbody tr').count()==count
        for href in page.locator('a').evaluate_all('(nodes)=>nodes.map(node=>node.getAttribute("href"))'):
            target=(root/unquote(href)).resolve()
            assert target.is_relative_to(root.resolve()) and target.is_file()
        page.locator('#search').fill('pyside6')
        assert page.locator('tbody tr:visible').count()==1
        page.locator('#search').fill('no-such-package')
        assert page.locator('tbody tr:visible').count()==0
        page.locator('#search').fill('')
        assert page.locator('tbody tr:visible').count()==count
        if args.screenshot:page.screenshot(path=str(args.screenshot))
        assert not errors,errors
    finally:browser.close()
print(f'License catalog verified: {count} rows, all notice links, filters, no JavaScript errors')
