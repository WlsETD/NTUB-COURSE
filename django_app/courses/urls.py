from django.urls import path

from . import views

app_name = "courses"
urlpatterns = [
    path("app/", views.app_page, name="app"),
    path("teacher/", views.teacher_page, name="teacher"),
    path("teacher/export.csv", views.teacher_export, name="teacher_export"),
    path("api/me/", views.api_me, name="me"),
    path("api/selection/", views.api_selection, name="selection"),
    path("api/selection/swap/", views.api_swap, name="swap"),
    path("api/applications/", views.api_apply, name="apply"),
    path("api/applications/<slug:request_id>/review/", views.api_review, name="review"),
    path("api/ai/depts/", views.api_ai_depts, name="ai_depts"),
    path("api/ai/suggest/", views.api_ai_suggest, name="ai_suggest"),
]
