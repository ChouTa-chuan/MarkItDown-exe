"""彙總 B3b3（舊旋轉，無 expand）與 B3b4（expand=True 旋轉）的評估結果。

輸入：
- B3b3 的 scan-evaluation-results.json（唯讀引用，不改寫）
- 本輪 expand-results.json（由 B3b3 的 run_scan_evaluation.py 產生）
輸出（stdout）：三種口徑的按語言字數加權正確率與逐條件編輯錯誤數。
口徑：
- 含舊旋轉：B3b3 的 12 個劣化條件（含無 expand 的兩個旋轉）
- 排除舊旋轉：B3b3 的 10 個非旋轉劣化條件
- 排除舊旋轉＋expand 旋轉：10 個非旋轉條件加上本輪兩個 expand=True 旋轉條件（12 條件）
計分沿用 B3b2／B3b 的按語言加總：正確率 = 1 − 總編輯距離／總參考字數。
原圖對照（clean）不計入加權彙總，只作對照列出。
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
B3B3 = HERE.parent/'b3b3-v5-provenance-scan-2026-11-20'/'scan-evaluation-results.json'
MODELS = ('v4-current', 'v5-rapid-mobile', 'v6-rapid-small')
OLD_ROTATIONS = ('rotate-0.8', 'rotate-2.0')
LANGS = ('zh-hant', 'zh-hans', 'en')


def totals(conditions, model):
    """把多個條件的 by_language 加總，回傳每語言的編輯數、參考字數與正確率。"""
    out = {}
    for lang in LANGS:
        edits = refs = 0
        for cond in conditions:
            row = cond['models'][model]['by_language'][lang]
            edits += row['edits']
            refs += row['reference_characters']
        out[lang] = dict(edits=edits, reference_characters=refs, accuracy=round(1 - edits/refs, 4))
    return out


def main(expand_path):
    old = json.loads(B3B3.read_text(encoding='utf-8'))['results']
    new = json.loads(Path(expand_path).read_text(encoding='utf-8'))['results']
    # 排除舊旋轉：B3b3 的非旋轉劣化條件。
    non_rotation = [v for k, v in old.items() if k not in ('clean',) + OLD_ROTATIONS]
    old_rot = [old[k] for k in OLD_ROTATIONS]
    expand = [new[k] for k in ('rotate-0.8-expand', 'rotate-2.0-expand')]
    views = {
        '含舊旋轉（B3b3 原口徑，12 條件）': old_rot + non_rotation,
        '排除舊旋轉（10 條件）': non_rotation,
        '排除舊旋轉＋expand 旋轉（12 條件）': non_rotation + expand,
    }
    summary = {}
    for name, conds in views.items():
        summary[name] = {m: totals(conds, m) for m in MODELS}
    per = {}
    for cond_id in list(old.keys()) + list(new.keys()):
        src = old if cond_id in old else new
        per[cond_id] = {m: {lang: src[cond_id]['models'][m]['by_language'][lang]['edits'] for lang in LANGS}
                        for m in MODELS}
    clean = {m: {lang: old['clean']['models'][m]['by_language'][lang]['edits'] for lang in LANGS} for m in MODELS}
    result = dict(views=summary, per_condition_edits=per, clean_edits=clean)
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    print()


if __name__ == '__main__':
    main(sys.argv[1])
