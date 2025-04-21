from django.shortcuts import render

from .models import User

def users_view(request):
    users = User.objects.all()
    context = {"users": users}
    return render(request, "users_list.html", context)

def user_detail_view(request, user_id):
    user = User.objects.get(id=user_id)
    context = {"user": user}
    return render(request, "user_detail.html", context)