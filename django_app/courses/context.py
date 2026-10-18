"""所有頁面共用的樣板變數。"""
from django.conf import settings


def store_mode(request):
    # STORE=memory 時頁面上方顯示提示，避免把本機記憶體裡的資料當成雲端的真實資料
    # dev_login：本機（DJANGO_DEBUG=1）登入頁顯示「測試登入」，正式環境不會出現
    return {"memory_store": settings.STORE == "memory", "dev_login": settings.DEBUG}
