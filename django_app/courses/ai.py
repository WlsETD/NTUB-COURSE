"""AI 選課建議：由伺服器組提示詞並呼叫 OpenAI。

API 金鑰只放在伺服器的 .env（OPENAI_API_KEY），不會傳到瀏覽器。
前端只送「學生的描述」與課程 id，提示詞由這裡組，避免有人拿這個端點去問別的事情。
"""
import json

from django.conf import settings

DEPT_ZH = {
    "401": "會計資訊系", "402": "財務金融系", "403": "財政稅務系", "404": "國際商務系", "405": "企業管理系",
    "406": "資訊管理系", "407": "應用外語系", "40A": "商業設計管理系", "40B": "創意科技與產品設計系", "40C": "數位多媒體設計系",
}
GRADE_ZH = ["", "大一", "大二", "大三", "大四"]
DAYS_ZH = ["", "一", "二", "三", "四", "五", "六", "日"]
MAX_CREDITS, MIN_CREDITS = 25, 9


class AIError(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


def enabled():
    return bool(settings.OPENAI_API_KEY)


def slot_text(slots):
    return "、".join(
        f"週{DAYS_ZH[d]} 第{s}節" if s == e else f"週{DAYS_ZH[d]} {s}–{e}節" for d, s, e in slots
    )


def _client():
    from openai import OpenAI
    return OpenAI(api_key=settings.OPENAI_API_KEY, timeout=90, max_retries=1)


def ask_json(prompt, model):
    """呼叫 OpenAI，要求只回 JSON 物件。"""
    import openai

    if not enabled():
        raise AIError("ai_unavailable")
    try:
        resp = _client().chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是國立臺北商業大學的選課顧問。只回覆一個 JSON 物件，不要其他文字。"},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )
    except openai.RateLimitError:
        raise AIError("rate_limited")
    except (openai.AuthenticationError, openai.PermissionDeniedError, openai.NotFoundError, openai.BadRequestError):
        raise AIError("ai_unavailable")  # 金鑰錯誤、模型名稱錯誤或帳戶沒有額度
    except openai.OpenAIError:
        raise AIError("ai_error")
    try:
        return json.loads(resp.choices[0].message.content or "{}")
    except (ValueError, IndexError, AttributeError):
        raise AIError("invalid_json")


def classify_depts(text, major):
    """第一步：把學生的描述對應到 1～3 個學系（例如「財務」→ 402、403）。"""
    prompt = (
        "把學生的描述對應到國立臺北商業大學四技日間部的學系。學系代碼："
        + "、".join(f"{k} {v}" for k, v in DEPT_ZH.items())
        + f"。\n學生本系是 {major} {DEPT_ZH.get(major, '')}。\n學生的描述：「{text[:800]}」\n"
        + '依相關程度挑 1 到 3 個學系；描述裡沒有明確領域時只回本系。只回覆 JSON：{"depts":["代碼"]}'
    )
    try:
        r = ask_json(prompt, settings.OPENAI_MODEL_FAST)
    except AIError as e:
        if e.code in ("rate_limited", "ai_unavailable"):
            raise
        r = {}
    raw = r.get("depts") if isinstance(r, dict) else None
    depts = []
    for d in raw if isinstance(raw, list) else []:
        d = str(d)
        if d in DEPT_ZH and d not in depts:
            depts.append(d)
    return depts[:3] or [major]


def suggest(text, student, depts, candidates, selected, lang):
    """第二步：從候選課程挑 3～6 門。candidates / selected 是課程 dict 的 list。"""
    total = sum(float(c["credits"]) for c in selected)
    mine = "、".join(f"{c['name']}（{slot_text(c['slots'])}，{c['credits']}學分）" for c in selected) or "無"
    lines = "\n".join(
        "|".join([c["id"], c["name"], c["type"], c["cls"], c["teacher"], slot_text(c["slots"]),
                  f"{c['credits']}學分", f"{c['enr']}/{c['cap']}"])
        for c in candidates
    )[:40000]
    prompt = (
        "你是國立臺北商業大學四技日間部的選課顧問。\n"
        f"學生：本系 {DEPT_ZH.get(student['major'], '')}，{GRADE_ZH[student['grade']]}，班級 {student['cls']}。\n"
        f"本學期已選：{mine}。目前共 {total:g} 學分；每學期上限 {MAX_CREDITS} 學分（超出不計），下限 {MIN_CREDITS} 學分。\n"
        f"學生想從這些學系選課：{'、'.join(DEPT_ZH[d] for d in depts)}（也可搭配通識）。\n"
        f"學生的興趣與目標：\n{text[:1500]}\n\n"
        "以下是目前可選、而且不和已選課程衝堂的候選課程，每行格式：id|課名|課別|開課班級|老師|時間|學分|已選/上限。\n"
        f"{lines}\n\n"
        f"請只從候選清單挑 3 到 6 門最適合的課：和學生目標相關的優先；挑出來的課彼此不能衝堂；加上已選學分最好不要超過 {MAX_CREDITS}；"
        "名額已滿或超額的課要在理由裡提醒會抽籤；也要尊重學生寫的時間偏好。\n"
        '只回覆一個 JSON 物件：{"summary":"兩三句整體建議","picks":[{"id":"候選清單裡的 id","reason":"一句具體理由"}],"notes":["需要注意的事，可以是空陣列"]}\n'
        + ("Write summary, reason and notes in English, but keep course names exactly as listed."
           if lang == "en" else "summary、reason、notes 都用繁體中文。")
    )
    r = ask_json(prompt, settings.OPENAI_MODEL)
    if not isinstance(r, dict):
        raise AIError("invalid_json")
    valid = {c["id"] for c in candidates}
    picks, seen = [], set()
    for x in r.get("picks") or []:
        cid = str((x or {}).get("id", "")) if isinstance(x, dict) else ""
        if cid in valid and cid not in seen:
            seen.add(cid)
            picks.append({"id": cid, "reason": str(x.get("reason") or "")[:300]})
    if not picks:
        raise AIError("invalid_json")
    notes = [str(n)[:300] for n in (r.get("notes") or []) if n][:4]
    return {"summary": str(r.get("summary") or "")[:600], "picks": picks[:6], "notes": notes}
