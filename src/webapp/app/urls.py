from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from home.views import home

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('users/', include('users.urls'), name='users'),
    path('', include('cuoora.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
