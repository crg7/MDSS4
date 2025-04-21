from abc import ABC, abstractmethod
from django.db.models import Count, Q
from .models import Inquiry

class BaseRetriever(ABC):
    def __init__(self, limit):
        self.limit = limit

    def fetch(self, user):
        qs = self.filter_qs(user)
        qs = qs.annotate(pos=Count('reactions', filter=Q(reactions__positive=True)))
        return qs.order_by('-pos')[:self.limit]

    @abstractmethod
    def filter_qs(self, user):
        pass

class SocialRetriever(BaseRetriever):
    def filter_qs(self, user):
        return user.following_inquiries()  # Asume método de tu lógica de “seguir”

class TopicsRetriever(BaseRetriever):
    def filter_qs(self, user):
        return user.inquiries_by_interests()

class NewsRetriever(BaseRetriever):
    def filter_qs(self, user):
        return Inquiry.objects.published_today()

class PopularRetriever(BaseRetriever):
    def filter_qs(self, user):
        return Inquiry.objects.popular_today()
