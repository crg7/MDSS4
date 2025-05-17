from rest_framework import serializers
from rest_framework.permissions import AllowAny
from user.models import Question, Answer


class QuestionSerializer(serializers.HyperlinkedModelSerializer):
    permission_classes = [AllowAny]
    class Meta:
        model = Question
        fields = ['id', 'title', 'description']

class AnswerSerializer(serializers.HyperlinkedModelSerializer):
    permission_classes = [AllowAny]
    class Meta:
        model = Answer
        fields = ['id', 'description']