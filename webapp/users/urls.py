from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path("list/", views.users_view),
    path("<int:user_id>/", views.user_detail_view),
    path("notifications/", views.notifications_view, name="notifications_view"),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)