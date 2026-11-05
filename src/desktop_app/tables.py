"""以實體儲存格幾何重建 PDF 表格；合併欄列必須有實際範圍證據。"""
from bisect import bisect_left, bisect_right
from dataclasses import dataclass
from html import escape
from math import isfinite


@dataclass(frozen=True)
class RenderedTable:
    text: str
    boxes: tuple
    warning: str
    claimed_char_ids: frozenset = frozenset()
    column_edges: tuple = ()
    first_row: tuple = ()
    row_count: int = 0


def _edges(values):
    groups=[]
    for value in sorted(values):
        if not groups or value-groups[-1][-1] > 0.5:
            groups.append([value])
        else:
            groups[-1].append(value)
    return [sum(group)/len(group) for group in groups]


def contains_char(char, box):
    x=(char['x0']+char['x1'])/2
    y=(char['top']+char['bottom'])/2
    return box[0] <= x < box[2] and box[1] <= y < box[3]


def _edge_index(edges,value):
    index=bisect_left(edges,value)
    return min({max(0,index-1),min(len(edges)-1,index)},key=lambda i:abs(edges[i]-value))


def render_table(page, table, checkpoint=lambda:None):
    checkpoint()
    from pdfplumber.utils import extract_text
    boxes=tuple(dict.fromkeys(tuple(cell) for cell in table.cells))
    fallback=RenderedTable('',(), '表格幾何不明確或超出處理上限；保留原生文字，未宣稱表格結構已還原。')
    if not boxes or len(boxes)>10000:
        return fallback
    if any(len(box)!=4 or not all(isfinite(value) for value in box) or
           box[0]>=box[2] or box[1]>=box[3] for box in boxes):
        return fallback
    xs=_edges([box[index] for box in boxes for index in (0,2)])
    ys=_edges([box[index] for box in boxes for index in (1,3)])
    if len(xs)<2 or len(ys)<2 or (len(xs)-1)*(len(ys)-1)>100000:
        return fallback
    if len(xs)==2:
        # 某些表單的單欄外框其實包住多欄文字；交還對齊分析，避免錯壓成一格。
        first=min(boxes,key=lambda box:(box[1],box[0]))
        header_words=page.crop(first).extract_words()
        header_words=sorted(header_words,key=lambda word:(word['top'],word['x0']))
        wide_gaps=sum(b['x0']-a['x1']>max(18,page.width*0.025) and abs(a['top']-b['top'])<=2
                      for a,b in zip(header_words,header_words[1:]))
        if wide_gaps>=2:
            return RenderedTable('',(),'單欄外框內可能含多欄文字，未壓成單欄表格；保留文字供對齊分析與核對。')
    owners={}; spans={}; contents={i:[] for i in range(len(boxes))}
    for index,box in enumerate(boxes):
        checkpoint()
        left,right=(_edge_index(xs,box[j]) for j in (0,2))
        top,bottom=(_edge_index(ys,box[j]) for j in (1,3))
        if left>=right or top>=bottom:
            return fallback
        spans[index]=(top,left,bottom-top,right-left)
        for row in range(top,bottom):
            for column in range(left,right):
                if (row,column) in owners:
                    return fallback
                owners[row,column]=index
    for number,char in enumerate(page.chars):
        if number%512==0:checkpoint()
        x=(char['x0']+char['x1'])/2;y=(char['top']+char['bottom'])/2
        slot=(bisect_right(ys,y)-1,bisect_right(xs,x)-1)
        owner=owners.get(slot)
        if owner is not None and contains_char(char,boxes[owner]):
            contents[owner].append(char)
    values={index:extract_text(chars) if chars else '' for index,chars in contents.items()}
    claimed=frozenset(id(char) for chars in contents.values() for char in chars)
    # 缺少實體儲存格不能當成合併證據；只有 cell 跨越網格才輸出 span。
    merged=any(rowspan>1 or colspan>1 for _,_,rowspan,colspan in spans.values())
    if merged:
        rows=['<table>']
        for row in range(len(ys)-1):
            checkpoint();cells=[]
            for column in range(len(xs)-1):
                owner=owners.get((row,column))
                if owner is None:
                    cells.append('<td></td>');continue
                top,left,rowspan,colspan=spans[owner]
                if (top,left)!=(row,column):continue
                attrs=(f' rowspan="{rowspan}"' if rowspan>1 else '')+(f' colspan="{colspan}"' if colspan>1 else '')
                cells.append(f'<td{attrs}>'+escape(values[owner]).replace('\n','<br>')+'</td>')
            rows.append('<tr>'+''.join(cells)+'</tr>')
        rows.append('</table>')
        return RenderedTable('\n'.join(rows),boxes,'依儲存格幾何輸出 HTML 合併表格；合併範圍與內容仍需核對原頁。',claimed)
    grid=[]
    for row in range(len(ys)-1):
        checkpoint()
        grid.append([escape(values[owners[row,column]]).replace('|','\\|').replace('\n','<br>')
                     if (row,column) in owners else '' for column in range(len(xs)-1)])
    rows=['| '+' | '.join(grid[0])+' |','| '+' | '.join(['---']*(len(xs)-1))+' |']
    rows += ['| '+' | '.join(row)+' |' for row in grid[1:]]
    header=tuple(values[owners[0,column]] if (0,column) in owners else '' for column in range(len(xs)-1))
    return RenderedTable('\n'.join(rows),boxes,'表格已擷取，首列按欄名輸出；請核對內容與欄列。',
                         claimed,tuple(xs),header,len(ys)-1)
