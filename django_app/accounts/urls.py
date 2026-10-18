from django.urls import path

from . import views

app_name = "accounts"
urlpatterns = [
    path("", views.login_page, name="login"),
    path("auth/session/", views.create_session, name="session"),
    path("auth/logout/", views.logout_view, name="logout"),
    path("dev/login/", views.dev_login, name="dev_login"),  # 只有 DEBUG 才有作用
]
