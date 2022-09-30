from rest_framework import serializers
from .models import Question, Answer


class QuestionListSerializer(serializers.ModelSerializer):
  author = serializers.CharField(source='author.username')
  class Meta:
    model = Question
    fields = '__all__'


class QuestionSerializerSub(serializers.ModelSerializer):
  class Meta:
    model = Question
    fields = ['id', 'title']

class QuestionRetrieveSerializer(serializers.ModelSerializer):
  author = serializers.CharField(source='author.username')
  class Meta:
    model = Question
    fields = '__all__'


class AnswerDetailSerializer(serializers.ModelSerializer):
  author = serializers.CharField(source='author.username')
  class Meta:
    model = Answer
    fields = ['id', 'author', 'content', 'created_at', 'updated_at']


class AnswerInputSerializer(serializers.ModelSerializer):

  class Meta:
    model = Answer
    fields = '__all__'

  def create(self, validated_data):
    answer = Answer.objects.create(**validated_data)
    return answer

class AnswerDeleteSerializer(serializers.ModelSerializer):
  class Meta:
    model = Answer
    fields = '__all__'


# question 전체를 보여주는 serializer
class QuestionDetailSerializer(serializers.Serializer):
  question = QuestionRetrieveSerializer()
  answerList =  AnswerDetailSerializer(many=True)


# question update/delete만 수행하는 serializer
class QuestionEditSerializer(serializers.ModelSerializer):
  class Meta:
    model = Question
    fields = '__all__'

    def update(self, instance, validated_data):
      instance.title = validated_data.get('title', instance.title)
      instance.content = validated_data.get('content', instance.content)
      instance.author = validated_data.get('author', instance.author)
      instance.save()
      return instance


class QuestionCreateSerializer(serializers.ModelSerializer):

  class Meta:
    model = Question
    fields = '__all__'

  def create(self, validated_data):
    question = Question.objects.create(**validated_data)
    return question


class QuestionDeleteSerializer(serializers.ModelSerializer):

  class Meta:
    model = Question
    fields = '__all__'