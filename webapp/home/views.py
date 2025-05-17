from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Count, Q, Max, Exists, OuterRef, Avg
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.views import LogoutView, LoginView
from django.contrib.auth import authenticate
from django.http import JsonResponse

from rest_framework.decorators import api_view

from tasks import analyze_text, send_notifications
from users.models import (
    Question, Answer, Vote, Topic, Notification,
    QuestionRetriever, SocialRetriever, TopicRetriever
)


@login_required(login_url='login')
def questions_list_view(request):
    recommender = request.GET.get('recommender', 'general')
    qs = (
        Question.objects
        .select_related('user')
        .prefetch_related('topics')
        .annotate(
            positive_votes_count=Count('votes', filter=Q(votes__is_positive_vote=True)),
            negative_votes_count=Count('votes', filter=Q(votes__is_positive_vote=False))
        )
        .filter(apto=True)
    )

    if recommender == 'social':
        preguntas = QuestionRetriever.create_social().retrieve_questions(qs, request.user)
    elif recommender == 'topic':
        preguntas = QuestionRetriever.create_topics().retrieve_questions(qs, request.user)
    elif recommender == 'news':
        today = timezone.localdate()
        preguntas = qs.filter(timestamp__date=today).order_by('-timestamp')
    elif recommender == 'popular':
        today = timezone.localdate()
        today_qs = qs.filter(timestamp__date=today)
        avg_likes = today_qs.aggregate(avg_likes=Avg('positive_votes_count'))['avg_likes'] or 0
        preguntas = (
            today_qs
            .filter(positive_votes_count__gte=avg_likes)
            .order_by('-positive_votes_count', '-timestamp')
        )
    else:
        preguntas = qs.order_by('-timestamp')

    return render(request, 'questions_list.html', {
        'preguntas': preguntas,
        'active_recommender': recommender,
    })


@api_view(['GET'])
@login_required
def api(request, id):
    pregunta = get_object_or_404(Question, pk=id)
    ct = ContentType.objects.get_for_model(Question)
    vote = (
        Vote.objects
        .filter(user=request.user, specific_subclass=ct, object_id=pregunta.id)
        .order_by('-timestamp')
        .first()
    )
    user_vote = None if not vote else ('like' if vote.is_positive_vote else 'dislike')
    data = {
        'title': pregunta.title,
        'description': pregunta.description,
        'username': pregunta.user.username,
        'timestamp': pregunta.timestamp.strftime('%d %B %Y %H:%M'),
        'topics': [t.name for t in pregunta.topics.all()],
        'positive_votes': pregunta.positive_votes().count(),
        'negative_votes': pregunta.negative_votes().count(),
        'user_vote': user_vote,
    }
    return JsonResponse(data)


@login_required(login_url='login')
def topics(request):
    order = request.GET.get('topic_order', 'popular')
    if order == 'recientes':
        qs = Topic.objects.order_by('-id')
    elif order == 'alfabetico':
        qs = Topic.objects.order_by('name')
    else:
        qs = Topic.objects.annotate(num_questions=Count('questions')).order_by('-num_questions')
    return render(request, 'topics.html', {
        'topics': qs,
        'active_topic_order': order,
    })


@login_required(login_url='login')
def responder_pregunta(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        contenido = request.POST.get('description')
        if contenido:
            answer = Answer.objects.create(
                user=request.user,
                question=question,
                description=contenido,
            )
            analyze_text.delay('answer', answer.id)
            Notification.objects.create(
                user=question.user,
                description=f"{request.user.username} has answered your question"
            )
            return redirect('responder_pregunta', pk=pk)

    ct = ContentType.objects.get_for_model(Answer)
    likes_qs = Vote.objects.filter(
        user=request.user,
        specific_subclass=ct,
        object_id=OuterRef('pk'),
        is_positive_vote=True
    )
    dislikes_qs = Vote.objects.filter(
        user=request.user,
        specific_subclass=ct,
        object_id=OuterRef('pk'),
        is_positive_vote=False
    )
    respuestas = (
        Answer.objects.filter(question=question)
        .annotate(
            positive_votes_count=Count('votes', filter=Q(votes__is_positive_vote=True)),
            negative_votes_count=Count('votes', filter=Q(votes__is_positive_vote=False)),
            user_liked=Exists(likes_qs),
            user_disliked=Exists(dislikes_qs),
        )
    )
    return render(request, 'responder_pregunta.html', {
        'question': question,
        'respuestas': respuestas,
        'active_tab': 'responder',
    })

class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')


class CustomLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True
    success_url = reverse_lazy('home')


def test_login(request):
    if request.method == 'POST':
        user = authenticate(
            request,
            username=request.POST.get('username'),
            password=request.POST.get('password'),
        )
        template = 'success.html' if user else 'error.html'
        context = {'user': user} if user else {'error': 'Usuario o contraseña incorrectos'}
        return render(request, template, context)
    return render(request, 'login_test.html')


@login_required(login_url='login')
def home_view(request):
    user = request.user
    mode = request.GET.get('recommender', 'general')
    qs = (
        Question.objects
        .select_related('user')
        .prefetch_related('topics')
        .annotate(
            positive_votes_count=Count('votes', filter=Q(votes__is_positive_vote=True)),
            negative_votes_count=Count('votes', filter=Q(votes__is_positive_vote=False))
        )
        .filter(apto=True)
    )
    if mode in ('news', 'reciente'):
        preguntas = qs.order_by('-timestamp')
    elif mode == 'popular':
        preguntas = qs.order_by('-positive_votes_count', '-timestamp')
    elif mode == 'social':
        preguntas = SocialRetriever().retrieve_questions(qs, user)
    elif mode in ('topic', 'relevante'):
        preguntas = TopicRetriever().retrieve_questions(qs, user)
    else:
        preguntas = list(qs)
    preguntas = preguntas[:4]

    order = request.GET.get('topic_order', 'popular')
    if order == 'recientes':
        topics = (
            Topic.objects
            .annotate(last_question_time=Max('questions__timestamp'))
            .order_by('-last_question_time')
        )
    elif order == 'alfabetico':
        topics = Topic.objects.order_by('name')
    else:
        topics = (
            Topic.objects
            .annotate(num_questions=Count('questions'))
            .order_by('-num_questions')
        )
    topics = topics[:4]
    return render(request, 'home.html', {
        'preguntas': preguntas,
        'topics': topics,
        'active_recommender': mode,
        'active_topic_order': order,
    })


def topic_detail(request, id):
    topic = get_object_or_404(Topic, pk=id)
    return JsonResponse({
        'id': topic.id,
        'name': topic.name,
        'description': topic.description,
        'num_preguntas': topic.questions.count(),
    })


@login_required
@require_POST
def api_question(request, id):
    user = request.user
    question = get_object_or_404(Question, pk=id)
    vote_type = request.POST.get('vote')
    ct = ContentType.objects.get_for_model(Question)
    existing = (
        Vote.objects
        .filter(user=user, specific_subclass=ct, object_id=question.id)
        .order_by('-timestamp')
        .first()
    )
    if existing and ((vote_type == 'like') == existing.is_positive_vote):
        existing.delete()
    else:
        if existing:
            existing.is_positive_vote = (vote_type == 'like')
            existing.save()
        else:
            Vote.objects.create(
                user=user,
                specific_subclass=ct,
                object_id=question.id,
                is_positive_vote=(vote_type == 'like')
            )
            Notification.objects.create(
                user=question.user,
                description=f"{user.username} has voted your question"
            )
    positive = question.votes.filter(is_positive_vote=True).count()
    negative = question.votes.filter(is_positive_vote=False).count()
    return JsonResponse({'positive_votes': positive, 'negative_votes': negative})


@login_required
@require_POST
def api_answer(request, id):
    answer = get_object_or_404(Answer, pk=id)
    vote_type = request.POST.get('vote')
    ct = ContentType.objects.get_for_model(Answer)
    existing = Vote.objects.filter(
        user=request.user,
        specific_subclass=ct,
        object_id=answer.id
    ).first()
    if existing and ((vote_type == 'like') == existing.is_positive_vote):
        existing.delete()
    else:
        if existing:
            existing.is_positive_vote = (vote_type == 'like')
            existing.save()
        else:
            Vote.objects.create(
                user=request.user,
                specific_subclass=ct,
                object_id=answer.id,
                is_positive_vote=(vote_type == 'like')
            )
            Notification.objects.create(
                user=answer.user,
                description=f"{request.user.username} has voted your answer"
            )
    positive = answer.votes.filter(is_positive_vote=True).count()
    negative = answer.votes.filter(is_positive_vote=False).count()
    return JsonResponse({'positive_votes': positive, 'negative_votes': negative})


@login_required(login_url='login')
def answers_list_view(request):
    ct = ContentType.objects.get_for_model(Answer)
    likes_qs = Vote.objects.filter(
        user=request.user,
        specific_subclass=ct,
        object_id=OuterRef('pk'),
        is_positive_vote=True
    )
    dislikes_qs = Vote.objects.filter(
        user=request.user,
        specific_subclass=ct,
        object_id=OuterRef('pk'),
        is_positive_vote=False
    )
    answers = (
        Answer.objects
        .annotate(
            positive_votes_count=Count('votes', filter=Q(votes__is_positive_vote=True)),
            negative_votes_count=Count('votes', filter=Q(votes__is_positive_vote=False)),
            user_liked=Exists(likes_qs),
            user_disliked=Exists(dislikes_qs),
        )
        .order_by('-timestamp')
    )
    return render(request, 'answers_list.html', {'answers': answers})


@login_required(login_url='login')
def crear_pregunta(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        topics_ids = request.POST.getlist('topics')
        if not title or not description:
            messages.error(request, 'Rellene Título y descripción')
        else:
            question = Question.objects.create(
                title=title,
                description=description,
                user=request.user,
                apto=True
            )
            send_notifications.delay(question.id)
            analyze_text.delay('question', question.id)
            question.topics.set(topics_ids)
            return redirect('questions_list')
    all_topics = Topic.objects.all()
    return render(request, 'crear_pregunta.html', {'topics': all_topics})
