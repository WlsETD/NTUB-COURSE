from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("app/", views.app_page, name="app"),
    path("teacher/", views.teacher_page, name="teacher"),
    path("api/me/", views.api_me, name="me"),
    path("api/selection/", views.api_selection, name="selection"),
    path("api/ai/depts/", views.api_ai_depts, name="ai_depts"),
    path("api/ai/suggest/", views.api_ai_suggest, name="ai_suggest"),
]
