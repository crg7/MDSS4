from django.db import models
from django.utils import timezone
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

User = get_user_model()

class Reaction(models.Model):
    """Registro genérico de voto positivo/negativo."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    positive = models.BooleanField(default=True)
    timestamp = models.DateTimeField(default=timezone.now)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{'👍' if self.positive else '👎'} by {self.user}"

class VotableBase(models.Model):
    """Abstracto para compartir votos y descripción."""
    description = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    reactions = GenericRelation(Reaction)

    class Meta:
        abstract = True

    def count_positive(self):
        return self.reactions.filter(positive=True).count()

    def count_negative(self):
        return self.reactions.filter(positive=False).count()

class InquiryManager(models.Manager):
    def published_today(self):
        today = timezone.now().date()
        return self.filter(timestamp__date=today)

    def popular_today(self):
        today_items = self.published_today()
        avg = today_items.aggregate(avg=models.Avg(models.F('reactions__positive')))['avg'] or 0
        return today_items.annotate(pos=models.Count('reactions', filter=models.Q(reactions__positive=True)))\
                          .filter(pos__gt=avg)

class Inquiry(VotableBase):
    """Pregunta principal."""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inquiries')
    categories = models.ManyToManyField('Category', related_name='inquiries')
    title = models.CharField(max_length=255)

    objects = InquiryManager()

    def __str__(self):
        return self.title

class Response(VotableBase):
    """Respuesta a una pregunta."""
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='responses')
    inquiry = models.ForeignKey(Inquiry, on_delete=models.CASCADE, related_name='responses')

    def __str__(self):
        return f"{self.author.username} → {self.inquiry.title[:30]}"

class Category(models.Model):
    """Tópicos o categorías de pregunta."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name
