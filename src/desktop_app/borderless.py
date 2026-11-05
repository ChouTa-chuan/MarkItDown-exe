"""依原生文字座標保守推測無框線表格；不確定處保留提醒與空格。"""
from bisect import bisect_right
from dataclasses import dataclass
from html import escape
import re
from statistics import median


@dataclass(frozen=True)
class InferredTable:
    top: float
    text: str
    claimed_char_ids: frozenset
    bbox: tuple
    column_edges: tuple
    first_row: tuple
    row_count: int


@dataclass(frozen=True)
class TextTableAnalysis:
    tables: list
    warnings: list
    words: list | None


def numeric(text):
    text=text.strip()
    if text.startswith('(')!=text.endswith(')'):return False
    return bool(re.fullmatch(r'\(?[+-]?\s*[$€£¥￥]?\s*\d[\d,.]*\s*(?:%|元)?\)?',text.strip()))


def _sparse_regions(rows,checkpoint):
    """以明確表頭的水平位置分欄，缺格保持空白，不自行向下填值。"""
    valid=[];used=set();budget=100_000;limited=False
    for start,header_cells in enumerate(rows):
        checkpoint()
        if budget<=0:
            limited=True;break
        if start in used or not 3<=len(header_cells)<=8:continue
        header=[' '.join(word['text'] for word in cell) for cell in header_cells]
        if any(numeric(value) or not any(c.isalpha() for c in value) or len(value)>45 for value in header):continue
        anchors=[cell[0]['x0'] for cell in header_cells]
        data=[];indices=[];intervals=[];last_top=header_cells[0][0]['top']
        for index in range(start+1,min(len(rows),start+257)):
            checkpoint()
            words=[word for cell in rows[index] for word in cell]
            budget-=len(words)
            if budget<=0:break
            if not words:break
            top=min(word['top'] for word in words)
            if not 0<top-last_top<=50:break
            assigned=[[] for _ in header]
            acceptable=True
            for word in words:
                column=bisect_right(anchors,word['x0']+4)-1
                if column<0 or (column+1<len(anchors) and word['x1']>anchors[column+1]-2):
                    acceptable=False;break
                assigned[column].append(word)
            if not acceptable or sum(bool(cell) for cell in assigned)<2:break
            if any(abs(cell[0]['x0']-anchors[column])>4 and
                   abs(cell[-1]['x1']-header_cells[column][-1]['x1'])>4
                   for column,cell in enumerate(assigned) if cell):break
            data.append([' '.join(word['text'] for word in cell) for cell in assigned])
            indices.append(index);last_top=top
            intervals.append((top,max(word['bottom'] for word in words),min(word['x0'] for word in words),max(word['x1'] for word in words)))
        if len(data)<2 or not any(not cell for row in data for cell in row):continue
        numeric_columns={column for row in data for column,cell in enumerate(row) if numeric(cell)}
        if len(numeric_columns)<2:continue
        header_words=[word for cell in header_cells for word in cell]
        header_interval=(min(w['top'] for w in header_words),max(w['bottom'] for w in header_words),min(w['x0'] for w in header_words),max(w['x1'] for w in header_words))
        intervals=[header_interval,*intervals]
        if any(intervals[i][1]>intervals[i+1][0] for i in range(len(intervals)-1)):continue
        spacing=[intervals[i+1][0]-intervals[i][0] for i in range(len(intervals)-1)]
        if max(spacing)/min(spacing)>1.8:continue
        grid=[[escape(value).replace('|','\\|') for value in row] for row in [header,*data]]
        text=['| '+' | '.join(grid[0])+' |','| '+' | '.join(['---']*len(header))+' |']
        text+=['| '+' | '.join(row)+' |' for row in grid[1:]]
        valid.append((intervals,'\n'.join(text),tuple([*anchors,header_cells[-1][-1]['x1']]),tuple(header),len(data)+1))
        used.update([start,*indices])
    return valid,used,limited


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
    # 表頭欄距可能較窄；依字高調整間距門檻，再以對齊與數值證據確認。
    gap=max(8,min(18,median(word['bottom']-word['top'] for word in words)*1.2)) if words else 18
    rows=[]
    for line in lines:
        cells=[]
        for word in sorted(line,key=lambda word:word['x0']):
            if not cells or word['x0']-cells[-1][-1]['x1']>gap:cells.append([word])
            else:cells[-1].append(word)
        rows.append(cells)
    valid,used,limited=_sparse_regions(rows,checkpoint)
    runs=[];current=[]
    for index,row in enumerate(rows):
        if index in used:
            if current:runs.append(current)
            current=[];continue
        if not 2<=len(row)<=8:
            if current:runs.append(current)
            current=[];continue
        if current and (len(current[-1])!=len(row) or row[0][0]['top']-current[-1][0][0]['top']>50):
            runs.append(current);current=[]
        current.append(row)
    if current:runs.append(current)
    warnings=['稀疏表格分析超過詞比對上限，未確認區域保留原生文字。'] if limited else []
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
        valid.append((intervals,'\n'.join(markdown),
                      tuple([cell[0]['x0'] for cell in run[0]]+[run[0][-1][-1]['x1']]),tuple(header),len(run)))
    # 僅認領已接受列內的字元，其餘正文繼續保留，避免整塊外框吞掉文字。
    spans=sorted((top,bottom,left,right,owner) for owner,(intervals,*_) in enumerate(valid)
                 for top,bottom,left,right in intervals)
    starts=[span[0] for span in spans];claimed=[set() for _ in valid]
    for index,char in enumerate(page.chars if valid else []):
        if index%512==0:checkpoint()
        x=(char['x0']+char['x1'])/2;y=(char['top']+char['bottom'])/2
        position=bisect_right(starts,y)-1
        if position>=0:
            top,bottom,left,right,owner=spans[position]
            if top<=y<=bottom and left<=x<=right:claimed[owner].add(id(char))
    tables=[InferredTable(intervals[0][0],text,frozenset(claimed[index]),
                          (min(row[2] for row in intervals),intervals[0][0],max(row[3] for row in intervals),intervals[-1][1]),
                          columns,header,count)
            for index,(intervals,text,columns,header,count) in enumerate(valid)]
    if tables:warnings.append('依文字對齊與數值欄推測無框線表格；首列與欄列仍需核對，未推測合併儲存格。')
    return TextTableAnalysis(tables,list(dict.fromkeys(warnings)),words)
