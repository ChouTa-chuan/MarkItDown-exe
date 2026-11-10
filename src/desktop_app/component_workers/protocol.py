"""C07 v1 有界 JSON-lines 協定；文件內容放結果檔，不放控制管道。"""
import json
import re

PROTOCOL = '1.0.0'
COMPONENT_ID = 'onnx-cpu-ocr'
COMPONENT_VERSION = '1.0.1'
# 只加入實際驗證且共用此協定的版本；不能因major相同就信任未知引擎。
SUPPORTED_COMPONENT_VERSIONS = frozenset(('1.0.0','1.0.1'))
MAX_FRAME = 16384
MAX_INPUT = 64*1024**2
MAX_RESULT = 8*1024**2
MAX_PIXELS = 16_000_000


class ProtocolError(ValueError):
    """版本、欄位、順序或長度不符，呼叫端停止該工作，不嘗試解讀任意輸出。"""


def unique(pairs):
    result = {}
    for key,value in pairs:
        if key in result:raise ProtocolError('重複的協定欄位。')
        result[key] = value
    return result


def require(condition, message='工作程序協定格式無效。'):
    if not condition:raise ProtocolError(message)


def encode(value):
    try:raw = (json.dumps(value,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode('utf-8')
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:raise ProtocolError('協定編碼失敗。') from exc
    require(len(raw)<=MAX_FRAME,'工作程序控制訊息過大。')
    return raw


def decode(raw):
    require(isinstance(raw,bytes) and 0<len(raw)<=MAX_FRAME and raw.endswith(b'\n'),'工作程序控制訊息截斷或過大。')
    try:value = json.loads(raw,object_pairs_hook=unique,parse_constant=lambda value:(_ for _ in ()).throw(ProtocolError('不接受非有限數值。')))
    except (ValueError,TypeError,UnicodeError,RecursionError) as exc:raise ProtocolError('無法解讀工作程序訊息。') from exc
    require(isinstance(value,dict) and value.get('protocol')==PROTOCOL,'不支援的工作程序協定。')
    return value


def fields(value, names):
    require(set(value)==set(names))


def identifier(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{32}',value))


def digest(value):
    require(isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value))


def limits(value):
    require(isinstance(value,dict))
    fields(value,('cpu_threads','max_pixels','max_output_bytes'))
    for name,minimum,maximum in (('cpu_threads',1,256),('max_pixels',1,MAX_PIXELS),('max_output_bytes',1024,MAX_RESULT)):
        require(type(value[name]) is int and minimum<=value[name]<=maximum)


def command(value):
    require(value.get('protocol')==PROTOCOL)
    kind = value.get('type')
    if kind=='run':
        fields(value,('protocol','type','job_id','operation','input','input_bytes','input_sha256','output','limits'))
        identifier(value['job_id']);limits(value['limits'])
        require(value['operation'] in ('ocr','health') and value['output']=='result.json')
        if value['operation']=='ocr':
            require(value['input']=='input.png' and type(value['input_bytes']) is int and 0<value['input_bytes']<=MAX_INPUT)
            digest(value['input_sha256'])
        else:require(value['input'] is None and value['input_bytes']==0 and value['input_sha256'] is None)
    else:
        fields(value,('protocol','type','job_id'))
        identifier(value['job_id'])
        require(kind in ('pause','resume','cancel'))
    return value


def component_version(value):
    require(isinstance(value,str) and value in SUPPORTED_COMPONENT_VERSIONS,'不支援此CPU元件版本。')
    return value


def event(value, *, expected_version=COMPONENT_VERSION):
    component_version(expected_version)
    require(value.get('protocol')==PROTOCOL)
    kind = value.get('type')
    if kind=='hello':
        fields(value,('protocol','type','component_id','component_version','pid','frozen','device'))
        require(value['component_id']==COMPONENT_ID and value['component_version']==expected_version
                and value['device']=='cpu' and type(value['pid']) is int and value['pid']>0 and type(value['frozen']) is bool)
    elif kind=='progress':
        fields(value,('protocol','type','job_id','stage'))
        identifier(value['job_id']);require(value['stage'] in ('loading','inference','export'))
    elif kind=='ready':
        fields(value,('protocol','type','job_id','providers'))
        identifier(value['job_id']);require(value['providers']==['CPUExecutionProvider']*3)
    elif kind=='completed':
        fields(value,('protocol','type','job_id','result','bytes','sha256'))
        identifier(value['job_id']);digest(value['sha256'])
        require(value['result']=='result.json' and type(value['bytes']) is int and 0<value['bytes']<=MAX_RESULT)
    elif kind in ('failed','cancelled'):
        fields(value,('protocol','type','job_id','code'))
        if value['job_id'] is not None:identifier(value['job_id'])
        require(isinstance(value['code'],str) and re.fullmatch('[a-z][a-z0-9_]{0,63}',value['code']))
    else:raise ProtocolError('未知工作程序事件。')
    return value


def result(value, job_id, *, expected_version=COMPONENT_VERSION):
    component_version(expected_version)
    require(isinstance(value,dict))
    fields(value,('schema_version','protocol','job_id','component_id','component_version','actual_device',
                  'providers','text','warning','input_sha256','health_passed','runtime'))
    require(type(value['schema_version']) is int and value['schema_version']==1 and value['protocol']==PROTOCOL
            and value['job_id']==job_id and value['component_id']==COMPONENT_ID
            and value['component_version']==expected_version and value['actual_device']=='cpu'
            and value['providers']==['CPUExecutionProvider']*3 and type(value['health_passed']) is bool)
    digest(value['input_sha256'])
    require(isinstance(value['text'],str) and isinstance(value['warning'],str) and len(value['warning'])<=2048)
    runtime = value['runtime'];require(isinstance(runtime,dict))
    fields(runtime,('python','rapidocr','onnxruntime','numpy','opencv','frozen'))
    require(runtime['rapidocr']=='1.4.4' and type(runtime['frozen']) is bool
            and all(isinstance(runtime[name],str) and 0<len(runtime[name])<=48 for name in ('python','rapidocr','onnxruntime','numpy','opencv')))
    return value
