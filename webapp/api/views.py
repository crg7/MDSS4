from rest_framework import routers, serializers, viewsets
from users.models import Question, Answer
from api.serializers import QuestionSerializer, AnswerSerializer
from tasks import send_notifications, analyze_text

class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def perform_create(self, serializer):
        print("Publishing a question..")
        instance = serializer.save()
        send_notifications.delay(instance.id)
        print("NEW Question!")

class AnswerViewSet(viewsets.ModelViewSet):
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer

    def perform_create(self, serializer):
        print("Publishing an answer..")
        instance = serializer.save()
        send_notifications.delay(instance.id)
        analyze_text.delay('answer', instance.id)
        print("NEW Answer!")