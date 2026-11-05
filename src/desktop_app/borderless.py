"""Conservative native-text table inference, with explicit uncertainty labels."""
from bisect import bisect_right
from dataclasses import dataclass
from html import escape
import re


@dataclass(frozen=True)
class InferredTable:
    top: float
    text: str
    claimed_char_ids: frozenset


@dataclass(frozen=True)
class TextTableAnalysis:
    tables: list
    warnings: list
    words: list | None


def numeric(text):
    text=text.strip()
    if text.startswith('(')!=text.endswith(')'):return False
    return bool(re.fullmatch(r'\(?[+-]?\s*[$€£¥￥]?\s*\d[\d,.]*\s*(?:%|元)?\)?',text.strip()))


def infer_tables(page,checkpoint=lambda:None):
    words=page.extract_words()
    if len(words)>20000:
        return TextTableAnalysis([],['文字對齊分析超出 20,000 詞上限，未推測無框線表格。'],None)
    lines=[]
    for index,word in enumerate(sorted(words,key=lambda word:(word['top'],word['x0']))):
        if index%256==0:checkpoint()
        if not lines or abs(word['top']-lines[-1][0]['top'])>2:
            lines.append([word])
        else:lines[-1].append(word)
    gap=max(18,page.width*0.025)
    rows=[]
    for line in lines:
        cells=[]
        for word in sorted(line,key=lambda word:word['x0']):
            if not cells or word['x0']-cells[-1][-1]['x1']>gap:cells.append([word])
            else:cells[-1].append(word)
        rows.append(cells)
    runs=[];current=[]
    for row in rows:
        if not 2<=len(row)<=8:
            if current:runs.append(current)
            current=[];continue
        if current and (len(current[-1])!=len(row) or row[0][0]['top']-current[-1][0][0]['top']>50):
            runs.append(current);current=[]
        current.append(row)
    if current:runs.append(current)
    valid=[];warnings=[]
    for run in runs:
        checkpoint()
        if len(run)<3:continue
        texts=[[' '.join(word['text'] for word in cell) for cell in row] for row in run]
        header=texts[0]
        if any(numeric(value) for value in header) or not all(any(c.isalpha() for c in value) for value in header):
            continue
        aligned=all(min(max(row[column][0]['x0'] for row in run)-min(row[column][0]['x0'] for row in run),
                        max(row[column][-1]['x1'] for row in run)-min(row[column][-1]['x1'] for row in run))<=4
                    for column in range(len(header)))
        numerical=any(sum(numeric(row[column]) for row in texts[1:])/len(texts[1:])>=0.8
                      for column in range(len(header)))
        intervals=[]
        for row in run:
            row_words=[word for cell in row for word in cell]
            intervals.append((min(word['top'] for word in row_words),max(word['bottom'] for word in row_words),
                              min(word['x0'] for word in row_words),max(word['x1'] for word in row_words)))
        spacing=[intervals[i+1][0]-intervals[i][0] for i in range(len(intervals)-1)]
        regular=min(spacing)>0 and max(spacing)/min(spacing)<=1.8
        nonoverlap=all(intervals[i][1]<=intervals[i+1][0] for i in range(len(intervals)-1))
        if not (aligned and numerical and regular and nonoverlap):
            warnings.append('偵測到對齊文字，但不足以確認無框線表格，未改寫為表格。')
            continue
        escaped=[[escape(value).replace('|','\\|') for value in row] for row in texts]
        markdown=['| '+' | '.join(escaped[0])+' |','| '+' | '.join(['---']*len(header))+' |']
        markdown+=['| '+' | '.join(row)+' |' for row in escaped[1:]]
        valid.append((intervals,'\n'.join(markdown)))
    # Associate only characters on accepted rows; prose outside them survives.
    spans=sorted((top,bottom,left,right,owner) for owner,(intervals,_) in enumerate(valid)
                 for top,bottom,left,right in intervals)
    starts=[span[0] for span in spans];claimed=[set() for _ in valid]
    for index,char in enumerate(page.chars if valid else []):
        if index%512==0:checkpoint()
        x=(char['x0']+char['x1'])/2;y=(char['top']+char['bottom'])/2
        position=bisect_right(starts,y)-1
        if position>=0:
            top,bottom,left,right,owner=spans[position]
            if top<=y<=bottom and left<=x<=right:claimed[owner].add(id(char))
    tables=[InferredTable(intervals[0][0],text,frozenset(claimed[index]))
            for index,(intervals,text) in enumerate(valid)]
    if tables:warnings.append('依文字對齊與數值欄推測無框線表格；首列與欄列仍需核對，未推測合併儲存格。')
    return TextTableAnalysis(tables,list(dict.fromkeys(warnings)),words)
