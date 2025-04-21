from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Inquiry, Response
from .retrievers import SocialRetriever, TopicsRetriever, NewsRetriever, PopularRetriever

def category_list(request):
    cats = Category.objects.all()
    return render(request, 'cuoora/categories.html', {'categories': cats})

def inquiry_detail(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk)
    if request.method == 'POST' and request.user.is_authenticated:
        desc = request.POST.get('description')
        if desc:
            Response.objects.create(author=request.user, inquiry=inquiry, description=desc)
        return redirect('inquiry_detail', pk=pk)
    return render(request, 'cuoora/inquiry_detail.html', {'inquiry': inquiry})

@login_required
def add_inquiry(request):
    if request.method == 'POST':
        title = request.POST['title']
        desc = request.POST['description']
        if title and desc:
            inq = Inquiry.objects.create(author=request.user, title=title, description=desc)
            # asignar categorías opcional...
        return redirect('social')
    return render(request, 'cuoora/add_inquiry.html')

def social(request):
    retr = SocialRetriever(limit=10)
    items = retr.fetch(request.user)
    return render(request, 'cuoora/social.html', {'inquiries': items})

def topics(request):
    retr = TopicsRetriever(limit=10)
    items = retr.fetch(request.user)
    return render(request, 'cuoora/topics.html', {'inquiries': items})

def news(request):
    retr = NewsRetriever(limit=10)
    items = retr.fetch(request.user)
    return render(request, 'cuoora/news.html', {'inquiries': items})

def popular(request):
    retr = PopularRetriever(limit=10)
    items = retr.fetch(request.user)
    return render(request, 'cuoora/popular.html', {'inquiries': items})
