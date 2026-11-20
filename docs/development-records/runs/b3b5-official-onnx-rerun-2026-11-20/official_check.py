"""B3b5：核對官方 PP-OCRv6 small 與 PP-OCRv5 mobile 的 ONNX 與 inference.yml，並建立外部字表檔。

背景：官方 ONNX 內沒有 metadata（沒有 character 字表）。RapidOCR 1.4.4 的 TextRecognizer
若 ONNX 沒有字表，就改讀 `rec_keys_path` 指定的檔案。字表來源是官方 inference.yml 的
PostProcess.character_dict。檔案格式是每行一個字元，UTF-8，以 \\n 結尾。

RapidOCR 會在讀入的字表前加 blank、後加一個空白，所以字表長度加 2 應等於 ONNX 的 CTC 輸出類別數。
本腳本逐項檢查這個關係，並用 RapidOCR 自己的 CTCLabelDecode 讀回字表，確認與 yml 完全相同。

輸入都由參數指定，檔案放在 repo 外（下載目錄），本腳本只讀取、不修改。
字表檔寫到參數指定的新檔（repo 外），repo 內只保留雜湊。
"""
import argparse
import hashlib
import json
from pathlib import Path

import onnxruntime as ort
import yaml
from rapidocr_onnxruntime.ch_ppocr_rec.utils import CTCLabelDecode

# 固定值來自 B3b4 sources.json 與本輪 HF 的 LFS／raw 取得結果。任何不符都停止。
PINS = {
    'v6': dict(name='PP-OCRv6 small rec', repo='PaddlePaddle/PP-OCRv6_small_rec_onnx',
               commit='b8f84f0b80c529de40b4fbb3544b84fa7233a513',
               onnx_sha256='5435fd747c9e0efe15a96d0b378d5bd157e9492ed8fd80edf08f30d02fa24634',
               onnx_bytes=21159378,
               yml_sha256='ab078671bb49f06228eadccd34f1bb501e157f7a047095ffb943ba81512c77d1',
               yml_bytes=150579),
    'v5': dict(name='PP-OCRv5 mobile rec', repo='PaddlePaddle/PP-OCRv5_mobile_rec_onnx',
               commit='ed152b8b495f84de93cda5709d768548a9127622',
               onnx_sha256='da72dc72ca4dc220df0dfde68c1dedc31c58d3e76a25871122e5056227d50092',
               onnx_bytes=16534782,
               yml_sha256='5dfeb2777f6d0db8177d8128a8acfcf6e6276dc4ac73ea3bf0dc06d6a5e85d8e',
               yml_bytes=148345),
}


def read_verified(path, digest, size):
    """讀取檔案並核對大小與 SHA-256；不符就丟出錯誤，不做任何後續處理。"""
    data = Path(path).read_bytes()
    if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
        raise ValueError(f'檔案與固定指紋不符：{path}')
    return data


def check_one(key, onnx_path, yml_path, chars_path):
    pin = PINS[key]
    read_verified(onnx_path, pin['onnx_sha256'], pin['onnx_bytes'])
    read_verified(yml_path, pin['yml_sha256'], pin['yml_bytes'])
    # 官方 yml 的字表。yaml.safe_load 只解析資料，不執行任何內容。
    official = [str(x) for x in yaml.safe_load(Path(yml_path).read_text(encoding='utf-8'))['PostProcess']['character_dict']]
    # 寫字表檔：每行一個字元，以 \n 結尾。若字元本身含換行，下面的回讀比對會失敗。
    Path(chars_path).write_text(''.join(f'{ch}\n' for ch in official), encoding='utf-8', newline='\n')
    chars_bytes = Path(chars_path).read_bytes()
    # 用 RapidOCR 自己的讀法回讀，並檢查 blank 與空白的位置。
    decoder = CTCLabelDecode(character_path=chars_path)
    character = decoder.character
    session = ort.InferenceSession(str(onnx_path), providers=['CPUExecutionProvider'])
    meta = session.get_modelmeta().custom_metadata_map
    classes = session.get_outputs()[0].shape[-1]
    checks = dict(
        rapidocr_reread_equals_yml=(character[1:-1] == official and character[0] == 'blank' and character[-1] == ' '),
        output_classes_equal_len_plus_2=(classes == len(character)),
    )
    if not all(checks.values()):
        raise ValueError(f'{key} 字表檢查失敗：{checks}, classes={classes}, len={len(character)}')
    return dict(
        name=pin['name'], repo=pin['repo'], commit=pin['commit'],
        onnx_sha256=pin['onnx_sha256'], onnx_bytes=pin['onnx_bytes'],
        yml_sha256=pin['yml_sha256'], yml_bytes=pin['yml_bytes'],
        onnx_metadata_keys=sorted(meta.keys()),
        onnx_input_shape=[str(d) for d in session.get_inputs()[0].shape],
        ctc_output_classes=classes,
        yml_character_entries=len(official),
        yml_contains_space_entry=(' ' in official),
        rapidocr_character_len_with_blank_and_space=len(character),
        chars_file_sha256=hashlib.sha256(chars_bytes).hexdigest(),
        chars_file_bytes=len(chars_bytes),
        checks=checks,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--onnx-v6', type=Path, required=True)
    parser.add_argument('--yml-v6', type=Path, required=True)
    parser.add_argument('--onnx-v5', type=Path, required=True)
    parser.add_argument('--yml-v5', type=Path, required=True)
    parser.add_argument('--chars-dir', type=Path, required=True, help='repo 外的字表輸出目錄（新目錄）')
    parser.add_argument('--output', type=Path, required=True, help='新的檢查結果 JSON，不覆蓋')
    args = parser.parse_args()
    args.chars_dir.mkdir(parents=True, exist_ok=True)
    result = dict(
        method='以固定 commit 的官方 ONNX 與 inference.yml 核對雜湊；由 yml 建字表檔，再以 RapidOCR 1.4.4 的 CTCLabelDecode 回讀比對。',
        onnx_has_embedded_character_metadata=None,
        models=dict(
            v6=check_one('v6', args.onnx_v6, args.yml_v6, args.chars_dir/'v6-official-keys.txt'),
            v5=check_one('v5', args.onnx_v5, args.yml_v5, args.chars_dir/'v5-official-keys.txt'),
        ),
    )
    result['onnx_has_embedded_character_metadata'] = any(
        'character' in m['onnx_metadata_keys'] for m in result['models'].values())
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
