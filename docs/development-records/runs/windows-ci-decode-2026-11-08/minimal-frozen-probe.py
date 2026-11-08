import json,sys,locale
print(json.dumps({'python_utf8_mode':bool(sys.flags.utf8_mode),'encoding':locale.getpreferredencoding(False),'message':'繁體／日本語／한국어'} ,ensure_ascii=False))
