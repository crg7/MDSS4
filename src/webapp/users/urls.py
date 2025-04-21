from django.urls import path

from . import views

urlpatterns = [
    path("list/", views.users_view),
    path("<int:user_id>/", views.user_detail_view)
]