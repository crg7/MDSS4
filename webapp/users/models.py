from abc import ABC, abstractmethod
from django.db import models
from django.db.models import Count, Q, Avg
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils import timezone


class User(AbstractUser):
    is_admin = models.BooleanField(default=False)
    topics_of_interest = models.ManyToManyField("Topic", related_name="users")
    following = models.ManyToManyField(
        "self", related_name="followers", blank=True
    )

    def add_topic(self, topic):
        self.topics_of_interest.add(topic)

    def get_votes(self):
        return self.votes.all()

    def add_question(self, question):
        self.questions.add(question)

    def get_questions(self):
        return self.questions.all()

    def follow(self, user):
        self.following.add(user)

    def stop_follow(self, user):
        self.following.remove(user)

    def get_answers(self):
        return self.answers.all()

    def get_following(self):
        return self.following.all()

    def add_vote(self, vote):
        self.votes.add(vote)

    def add_answer(self, answer):
        self.answers.add(answer)

    def get_topics_of_interest(self):
        return self.topics_of_interest.all()

    def calculate_score(self):
        question_score = sum(
            10 for q in self.questions.all()
            if q.positive_votes().count() > q.negative_votes().count()
        )
        answer_score = sum(
            20 for a in self.answers.all()
            if a.positive_votes().count() > a.negative_votes().count()
        )
        return question_score + answer_score


class Votable(models.Model):
    votes = GenericRelation(
        'Vote',
        content_type_field='specific_subclass',
        object_id_field='object_id',
        related_query_name='votable'
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

    def _filter_votes(self, is_positive):
        return self.votes.filter(is_positive_vote=is_positive)

    def positive_votes(self):
        return self._filter_votes(True)

    def negative_votes(self):
        return self._filter_votes(False)

    def add_vote(self, vote):
        if self.votes.filter(pk=vote.pk).exists():
            raise ValueError("User has already voted.")
        self.votes.add(vote)

    def get_votes(self):
        return self.votes.all()


class Answer(Votable):
    description = models.TextField()
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(
        "Question", on_delete=models.CASCADE, related_name="answers"
    )
    apto = models.BooleanField(null=True, default=None)

    def __str__(self):
        return f"In response to <<{self.question.title}>> by {self.user.username}"


class Topic(models.Model):
    name = models.CharField(max_length=75)
    description = models.TextField()

    def add_question(self, question):
        self.questions.add(question)

    def get_questions(self):
        return self.questions.all()

    def __str__(self):
        return self.name


class Question(Votable):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="questions"
    )
    topics = models.ManyToManyField(
        Topic, related_name="questions"
    )
    apto = models.BooleanField(null=True, default=None)

    def get_topics(self):
        return self.topics.all()

    def add_topic(self, topic):
        if self.topics.filter(pk=topic.pk).exists():
            raise ValueError("Topic already added.")
        self.topics.add(topic)

    def get_best_answer(self):
        if not self.answers.exists():
            return None
        return max(
            self.answers.all(),
            key=lambda a: a.positive_votes().count() - a.negative_votes().count()
        )

    def __str__(self):
        return self.title


class Vote(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="votes"
    )
    specific_subclass = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="votes"
    )
    object_id = models.PositiveIntegerField()
    votable = GenericForeignKey('specific_subclass', 'object_id')
    is_positive_vote = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (
            ("user", "specific_subclass", "object_id"),
        )

    def is_like(self):
        return self.is_positive_vote

    def like(self):
        self.is_positive_vote = True

    def dislike(self):
        self.is_positive_vote = False

    def __str__(self):
        return f"By {self.user.username}"


class QuestionRetrievalStrategy(ABC):
    @abstractmethod
    def retrieve_questions(self, questions, user):
        pass


class SocialRetriever(QuestionRetrievalStrategy):
    def retrieve_questions(self, questions_qs, user):
        following_ids = user.following.values_list('id', flat=True)
        return questions_qs.filter(
            user__id__in=following_ids
        ).annotate(
            positive_votes_count=Count(
                'votes', filter=Q(votes__is_positive_vote=True)
            )
        ).order_by('-positive_votes_count', '-timestamp')


class TopicRetriever(QuestionRetrievalStrategy):
    def retrieve_questions(self, questions, user):
        topics_questions = []
        for topic in user.topics_of_interest.all():
            topics_questions.extend(topic.questions.all())
        sorted_q = sorted(
            topics_questions,
            key=lambda q: q.positive_votes().count()
        )
        return [
            q for q in sorted_q[-min(100, len(sorted_q)):]
            if q.user != user
        ]


class NewsRetriever(QuestionRetrievalStrategy):
    def retrieve_questions(self, questions, user):
        today = timezone.localdate()
        if hasattr(questions, 'filter'):
            return [
                q for q in questions.filter(
                    timestamp__date=today
                ) if q.user != user
            ]
        return [
            q for q in questions
            if timezone.localtime(q.timestamp).date() == today and q.user != user
        ]


class PopularTodayRetriever(QuestionRetrievalStrategy):
    def retrieve_questions(self, questions, user):
        today = timezone.localdate()
        if hasattr(questions, 'annotate'):
            qs = questions.filter(
                timestamp__date=today
            ).annotate(
                positive_votes_count=Count(
                    'votes', filter=Q(votes__is_positive_vote=True)
                )
            )
            avg_likes = qs.aggregate(
                avg_likes=Avg('positive_votes_count')
            )['avg_likes'] or 0
            return list(
                qs.filter(
                    positive_votes_count__gte=avg_likes
                ).order_by('-positive_votes_count', '-timestamp')
            )
        today_qs = [
            q for q in questions
            if timezone.localtime(q.timestamp).date() == today
        ]
        if not today_qs:
            return []
        avg_likes = (
            sum(q.positive_votes().count() for q in today_qs)
            / len(today_qs)
        )
        popular = [
            q for q in today_qs
            if q.positive_votes().count() >= avg_likes and q.user != user
        ]
        return sorted(
            popular,
            key=lambda q: q.positive_votes().count(),
            reverse=True
        )


class QuestionRetriever:
    @classmethod
    def create_social(cls):
        return SocialRetriever()

    @classmethod
    def create_topics(cls):
        return TopicRetriever()

    @classmethod
    def create_news(cls):
        return NewsRetriever()

    @classmethod
    def create_popular_today(cls):
        return PopularTodayRetriever()


class Notification(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="notifications"
    )
    description = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.description
