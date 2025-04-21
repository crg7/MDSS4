from django.urls import path
from . import views

urlpatterns = [
    path('categories/', views.category_list, name='categories'),
    path('social/', views.social, name='social'),
    path('topics/', views.topics, name='topics'),
    path('news/', views.news, name='news'),
    path('popular/', views.popular, name='popular'),
    path('inquiries/add/', views.add_inquiry, name='add_inquiry'),
    path('inquiries/<int:pk>/', views.inquiry_detail, name='inquiry_detail'),
]
