"""所有頁面共用的樣板變數。"""
from django.conf import settings


def store_mode(request):
    # STORE=memory 時頁面上方顯示提示，避免把本機記憶體裡的資料當成雲端的真實資料
    return {"memory_store": settings.STORE == "memory"}
