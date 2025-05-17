from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from home.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('home/', home_view, name='home'),
    path('users/', include('users.urls')),
    path('questions/', questions_list_view, name='questions_list'),
    path('pregunta/crear/', crear_pregunta, name='crear_pregunta'),
    path('pregunta/<int:pk>/responder/', responder_pregunta, name='responder_pregunta'),
    path('topics/', topics, name='topics'),
    path('answers/', answers_list_view, name='answers_list'),
    path('api/topic/<int:id>/', topic_detail, name='topic_api'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
