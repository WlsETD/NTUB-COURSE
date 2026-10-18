"""從學校信箱的學號判斷學制、科系、年級。

北商日間部學號：入學學年度 3 碼 + 學制 1 碼 + 科系 1 碼 + 流水號，例如 11446001
（114 學年度入學、4 = 四技、6 = 資訊管理系）。也接受科系前面多一個 0 的寫法（114406001）。
課程資料的學系代碼是「學制 4 + 0 + 科系」，所以四技資管 = 406。

課程資料只有四技日間部（115-1），其他學制或看不懂的帳號回傳 None，前端就照舊讓學生自己選。
"""
import re

TERM_YEAR = 115  # 課程資料的學年度（data/ntub_115-1.txt）

PROGRAMS = {"4": "四技", "3": "二技"}
DEPT_CODES = set("1234567ABC")  # 401～407、40A～40C

_ID = re.compile(r"^(\d{3})([34])0?([0-9A-C])(\d{3,4})$")


def parse_student_id(sid):
    """學號 → {"sid","year","program","programName","dept","grade"}；不是日間部學號則回傳 None。"""
    sid = (sid or "").strip().upper()
    m = _ID.match(sid)
    if not m:
        return None
    year, program, dept, _serial = m.groups()
    year = int(year)
    if dept not in DEPT_CODES or year > TERM_YEAR:
        return None
    info = {"sid": sid, "year": year, "program": program, "programName": PROGRAMS[program], "dept": None, "grade": None}
    if program == "4":  # 課程資料只有四技
        info["dept"] = "40" + dept
        info["grade"] = min(4, max(1, TERM_YEAR - year + 1))  # 超過四年（延畢）算大四
    return info


def student_from_email(email):
    return parse_student_id((email or "").split("@")[0])
