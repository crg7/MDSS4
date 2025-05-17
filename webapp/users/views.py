from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from .models import User, Notification

def users_view(request):
    users = User.objects.all()
    return render(request, "users_list.html", {"users": users})

def user_list(request):
    users = User.objects.all()
    return render(request, "users_list.html", {"users": users})

def user_detail_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    return render(request, "user_detail.html", {"user": user})

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by("timestamp")
    return render(request, "notifications.html", {"notifications": notifications})
