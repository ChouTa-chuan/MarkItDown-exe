"""Conservative continuation hints; never merge or remove source rows."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class TableFragment:
    page: int
    identifier: str
    width: float
    height: float
    bbox: tuple
    columns: tuple
    header: tuple
    rows: int
    boundary_text: str = ''


def boundary_has_content(text):
    page_number=re.compile(r'(?:\d+(?:\s*[/／]\s*\d+)?|Page\s+\d+(?:\s+of\s+\d+)?|第\s*\d+\s*頁)',re.IGNORECASE)
    return any(line.strip() and not page_number.fullmatch(line.strip()) for line in text.splitlines())


def possible_continuation(previous,current):
    if previous is None or current.page!=previous.page+1:
        return False
    if min(previous.width,current.width,previous.height,current.height)<=0:
        return False
    if previous.bbox[3] < previous.height*0.9 or current.bbox[1] > current.height*0.12:
        return False
    if previous.rows<2 or current.rows<2 or len(current.header)<2:
        return False
    if len(previous.columns)!=len(current.columns) or len(current.columns)!=len(current.header)+1:
        return False
    if len(previous.header)!=len(current.header):
        return False
    left=tuple(' '.join(value.split()) for value in previous.header)
    right=tuple(' '.join(value.split()) for value in current.header)
    if left!=right or not all(right) or not any(char.isalpha() for value in right for char in value):
        return False
    if any(abs(a/previous.width-b/current.width)>0.005 for a,b in zip(previous.columns,current.columns)):
        return False
    return not boundary_has_content(previous.boundary_text) and not boundary_has_content(current.boundary_text)


def boundary_text(page,bbox,tail):
    from pdfplumber.utils import extract_text
    chars=[char for char in page.chars if ((char['top']+char['bottom'])/2 > bbox[3] if tail
                                         else (char['top']+char['bottom'])/2 < bbox[1])]
    return extract_text(chars) if chars else ''
