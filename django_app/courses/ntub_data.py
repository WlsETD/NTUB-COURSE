"""北商課程資料：讀取 data/ntub_115-1.txt，轉成前端使用的 RAW 格式。

RAW 每筆：[id, 學系, src, 班級, 年級, 課號, 課名, 老師, slots, 教室, 學分, 名額, 已選, 課別, cat, icon]
- src：dept 本系課、ge 通識、pe 體育、mil 軍訓
- slots：[[星期, 起始節, 結束節], ...]
- Django 輸出給前端時，最後另附可選的 approval_kind（舊資料不限制）。
"""
import re
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "ntub_115-1.txt"

FIELDS = ["id", "dept", "src", "cls", "grade", "code", "name", "teacher", "slots", "room", "credits", "cap", "enr", "type", "cat", "icon"]


def required_application_kind(course, major):
    kind = course.get("approval_kind", "")
    if kind == "cross_dept" and (course["src"] != "dept" or course["dept"] == major):
        return ""
    return kind if kind in ("add", "cross_dept", "prerequisite") else ""

GN={'一':1,'二':2,'三':3,'四':4}
KW=[('code',['程式','Python','網頁','網站','應用程式','遊戲開發']),('lock',['資安','資訊安全','安全']),('tree',['資料結構','資料庫']),
 ('neural',['人工智慧','AI','機器','大數據','資料科學','數據','智能']),('cloud',['雲端','虛擬化']),('terminal',['作業系統','伺服器','流程自動化','Linux']),
 ('chip',['計算機','電腦','物聯網','感測','資訊網路','資訊系統','軟體','科技程式']),('globe',['國際','全球','跨境','區域','跨文化','歐洲','貿易','外匯']),
 ('calc',['會計','審計','稅','成本','財報','財務報表']),('chart',['經濟','統計','投資','財務','金融','證券','期貨','貨幣','銀行','財金','財政','保險','資產','市場']),
 ('scale',['法','救濟','治理','專利']),('dice',['機率']),('integral',['微積分','數學']),('film',['動畫','影片','影像','多媒體','電影','劇本','渲染','後製']),
 ('palette',['設計','素描','繪圖','插畫','造形','色彩','美術','藝術','攝影','編輯','繪本','雕塑','模型','美學']),('torii',['日語','日文','韓語','越南','泰國','西班牙','華語']),
 ('speech',['英文','英語','溝通','簡報','談判','書信']),('book',['國文','中文','文學','寫作','閱讀','字彙','語言','翻譯']),
 ('shield',['軍訓','國防']),('shuttle',['羽球']),('yoga',['瑜伽','太極']),('wave',['划船','游泳','海洋']),('ball',['籃球','排球','棒壘','網球','桌球','匹克','撞球']),
 ('music',['舞','Hiphop','配樂','音樂']),('run',['健身','健走','休閒','射箭','體育']),('flag',['專題','實習','講座']),
 ('leaf',['永續','綠','環境','自然','生物','生命','食品','氣象']),('mind',['心理','人因']),('bulb',['哲學','思維','創意','創業','思考','人生','導論']),
 ('people',['管理','人力','人際','行銷','消費者','顧客','企業','策略','組織','公民','民主','社會','性別','人權','職場','服務','通路','供應鏈','運籌','生涯','經營']),
 ('atom',['科技','實境','3D','動力','機械'])]
def icon_for(n):
    for ic,ws in KW:
        if any(w in n for w in ws):return ic
    return 'book'
REQ={'專必','院必','校必','共必','核必','一般'}

def parse_rows(lines):
    """把資料檔的每一行轉成 RAW 格式的 list（和前端 course.html 用的一樣）。"""
    rows=[l.split('|') for l in lines if l.strip()]
    data=[]
    for i,r in enumerate(rows):
        d,cls,code,name,tch,times,room,cr,cap,enr,typ=r
        if d in ('400','901','903'):
            src={'400':'ge','901':'pe','903':'mil'}[d]
            m=re.search(r'四([甲乙丙])',cls) if d=='901' else None
            grade=4 if (d=='901' and '選項四' in cls) else 0
        else:
            src='dept';m=re.search(r'([一二三四])年',cls);grade=GN[m.group(1)]
        per={}
        for tok in times.split():
            per.setdefault(int(tok[0]),[]).append(int(tok[1:]))
        slots=[]
        for day in sorted(per):
            ps=sorted(per[day]);st=ps[0];pv=ps[0]
            for x in ps[1:]+[None]:
                if x is not None and x==pv+1:pv=x;continue
                slots.append([day,st,pv])
                if x is not None:st=pv=x
        cat='req' if typ in REQ else ('ge' if typ=='通必' else 'ele')
        crf=float(cr);crf=int(crf) if crf.is_integer() else crf
        data.append(['s%d'%i,d,src,cls,grade,code,name,tch,slots,room,crf,int(cap),int(enr),typ,cat,icon_for(name)])
    return data


def load_rows(path=DATA_FILE):
    return parse_rows(Path(path).read_text(encoding="utf8").split("\n"))


def to_dict(row):
    return dict(zip(FIELDS, row))


def to_row(d):
    return [d[f] for f in FIELDS]
