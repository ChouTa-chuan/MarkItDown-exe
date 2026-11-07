"""Tesseract 四語契約；混合解碼不是自動語言分類，也不宣告 ONNX 日韓品質。"""
import json
from importlib.resources import files

LANGUAGES = {'chi_tra':'繁體中文','eng':'英文','jpn':'日文','kor':'韓文'}
PRESETS = [('相容預設：繁中／英文（沿用舊行為）','legacy'),
           ('繁中＋英文','chi_tra+eng'),('英文','eng'),('日文','jpn'),('韓文','kor'),
           ('日文＋英文','jpn+eng'),('韓文＋英文','kor+eng'),
           ('繁中＋英文＋日文＋韓文（混合解碼）','chi_tra+eng+jpn+kor')]


def validate_languages(value):
    if value is None:return  # 保留舊版只選本機可用繁中／英文並提示缺語言的行為。
    if (not isinstance(value,tuple) or not 1<=len(value)<=4
            or any(not isinstance(name,str) or name not in LANGUAGES for name in value)
            or len(set(value))!=len(value)):
        raise ValueError('OCR 語言須為不重複的 chi_tra／eng／jpn／kor 清單。')


def parse_languages(value):
    result=None if value=='legacy' else tuple(value.split('+'))
    validate_languages(result);return result


def model_manifest():
    return json.loads(files('desktop_app').joinpath('data/ocr-four-languages.json').read_text(encoding='utf-8'))
