
from django.urls import path
from . import views

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("upload/", views.upload, name="upload"),
    path("batch/<int:pk>/", views.batch_detail, name="batch"),
    path("item/<int:pk>/", views.item_edit, name="item"),
    path("item/<int:pk>/title/", views.title_suggest, name="title_suggest"),
    path("photo/<int:pk>/move/", views.move_photo, name="move_photo"),
    path("photo/<int:pk>/view/", views.view_photo, name="view_photo"),
    path("item/<int:pk>/ai-generate/", views.ai_generate, name="ai_generate"),
    path("item/<int:pk>/approve/", views.approve, name="approve"),
]
