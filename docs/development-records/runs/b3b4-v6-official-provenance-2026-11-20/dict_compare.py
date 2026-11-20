"""比較官方 inference.yml 的 PostProcess.character_dict 與 RapidOCR 轉檔 ONNX 內嵌字表（metadata character）。

輸入（皆由參數指定，repo 外）：官方 inference.yml（固定 commit 取得）與候選 ONNX。
只讀取 yml 的字表與 ONNX 的 metadata；不做推論以外的執行。
輸出 JSON 到 stdout：字數、順序是否完全相同、集合差異、位置差異數。
注意：yml 與 ONNX 的字表相同，只說明字表內容一致；不代表 ONNX 權重與官方檔相同。
"""
import argparse
import json
from pathlib import Path

import onnxruntime as ort
import yaml


def official_dict(yml_path):
    data = yaml.safe_load(Path(yml_path).read_text(encoding='utf-8'))
    return [str(x) for x in data['PostProcess']['character_dict']]


def embedded_dict(onnx_path):
    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
    meta = session.get_modelmeta().custom_metadata_map
    lines = meta.get('character', '').split('\n')
    return lines, session.get_outputs()[0].shape[-1]


def compare(name, yml_list, onnx_path):
    rapid, classes = embedded_dict(onnx_path)
    same_order = rapid == yml_list
    return dict(
        candidate=name,
        yml_entries=len(yml_list),
        onnx_metadata_lines=len(rapid),
        onnx_ctc_output_classes=classes,
        identical_order_and_content=same_order,
        positional_differences=sum(1 for a, b in zip(rapid, yml_list) if a != b),
        only_in_onnx=sorted(set(rapid) - set(yml_list))[:20],
        only_in_yml=sorted(set(yml_list) - set(rapid))[:20],
        yml_first_entries=yml_list[:3],
        yml_last_entries=yml_list[-2:],
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--yml-v6', type=Path, required=True)
    parser.add_argument('--yml-v5', type=Path, required=True)
    parser.add_argument('--onnx-v6', type=Path, required=True)
    parser.add_argument('--onnx-v5', type=Path, required=True)
    args = parser.parse_args()
    v6 = official_dict(args.yml_v6)
    v5 = official_dict(args.yml_v5)
    result = dict(
        method='官方 inference.yml PostProcess.character_dict 與 RapidOCR ONNX metadata character 逐行比較',
        official_v6_vs_rapid_v6=compare('PP-OCRv6 small rec', v6, args.onnx_v6),
        official_v5_vs_rapid_v5=compare('PP-OCRv5 mobile rec', v5, args.onnx_v5),
        official_v6_dict_equals_official_v5_dict=(v6 == v5),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
