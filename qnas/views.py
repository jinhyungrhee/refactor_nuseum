from accounts.models import User
from rest_framework.generics import CreateAPIView, RetrieveAPIView, DestroyAPIView, UpdateAPIView, RetrieveDestroyAPIView
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from .models import Question, Answer
from .serializers import AnswerInputSerializer, QuestionCreateSerializer, QuestionListSerializer, QuestionDetailSerializer, QuestionEditSerializer, QuestionDeleteSerializer, AnswerDeleteSerializer
from rest_framework.response import Response
from rest_framework import status

class CustomPagination(PageNumberPagination):
  page_size = 20

# Question List & Create
class QuestionAPIView(APIView):
  def get(self, request):
    paginator = CustomPagination()
    # 관리자 계정이면 전체 question 출력
    if self.request.user.is_superuser == True or self.request.user.is_staff == True:
      questions = Question.objects.all().order_by('-created_at')
    # 일반 유저 계정이면 자기 question만 출력
    else:
      questions = Question.objects.filter(author=request.user).order_by('-created_at') # anonymous 유저 예외처리 필요없음(원래 레포에서는 모든 api 접근 막기 때문)
    results = paginator.paginate_queryset(questions, request)
    question_serializer = QuestionListSerializer(results, many=True, context={"request":request})
    return paginator.get_paginated_response(question_serializer.data)

  def post(self, request):
    if not request.user.is_authenticated:
      return Response(status=status.HTTP_401_UNAUTHORIZED)
    serializer = QuestionCreateSerializer(data=request.data)
    # print(dir(serializer))
    if serializer.is_valid():
      question = serializer.save(author=request.user)
      question_serializer = QuestionCreateSerializer(question).data
      return Response(data=question_serializer, status=status.HTTP_200_OK)
    else:
      return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Question Detail
class QuestionDetailAPIView(RetrieveAPIView):
  queryset = Question.objects.all()
  serializer_class = QuestionDetailSerializer

  def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    #  prevInstance, nextInstance = get_prev_next(instance)
    # 접근 권한 제한
    if self.request.user != instance.author and self.request.user.is_superuser != True: # 후에 is_staff 추가
      data = {
        'vallidation_error' : '작성자 본인 또는 관리자만 조회할 수 있습니다.'
      }
      return Response(data=data, status=status.HTTP_401_UNAUTHORIZED)
    answerList = instance.answer_set.all() # 현재 question에 달려있는 answer 전부 가져오는 ORM 쿼리문
    data = {
    'question' : instance,
    'answerList' : answerList,
    }
    serializer = self.get_serializer(instance=data)
    return Response(serializer.data)

# Question Update
class QuestionUpdateAPIView(UpdateAPIView):
  queryset = Question.objects.all()
  serializer_class = QuestionEditSerializer

  def put(self, request, *args, **kwargs):
    return self.update(request, *args, **kwargs)

  def update(self, request, *args, **kwargs):
    partial = kwargs.pop('partial', False)
    instance = self.get_object()
    # 본인만 수정 가능하도록 접근 권한 설정
    if instance.author != self.request.user:
      data = {
        'validation_err' : '작성자 본인만 수정할 수 있습니다.'
      }
      return Response(data=data, status=status.HTTP_401_UNAUTHORIZED)
    serializer = self.get_serializer(instance, data=request.data, partial=partial)
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)

    if getattr(instance, '_prefetched_objects_cache', None):
        # If 'prefetch_related' has been applied to a queryset, we need to
        # forcibly invalidate the prefetch cache on the instance.
        instance._prefetched_objects_cache = {}

    return Response(serializer.data)

  # def patch(self, request, *args, **kwargs):
  #   return self.partial_update(request, *args, **kwargs)

# Answer Create
class AnswerCreateAPIView(CreateAPIView):
  queryset = Answer.objects.all()
  serializer_class = AnswerInputSerializer

  def post(self, request, pk):
        return self.create(request, pk)

  def create(self, request, pk):
        if self.request.user.is_superuser == True or self.request.user.is_staff == True:
          # admin, staff 유저가 답변 작성시 question의 is_answered 필드 True로 변경 ("답변 완료!")
          Question.objects.filter(pk=pk).update(is_answered=True)
        author = User.objects.get(username=self.request.user)
        answer_data = {
          'question' : pk,
          'author' : author.id,
          'content' : request.data['content']
        }
        serializer = self.get_serializer(data=answer_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # print(serializer.data) # dict
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

  def perform_create(self, serializer):
      serializer.save()

# Question Delete
class QuestionDeleteAPIView(DestroyAPIView):
  queryset = Question.objects.all()
  serializer_class = QuestionDeleteSerializer

  def delete(self, request, *args, **kwargs):
    return self.destroy(request, *args, **kwargs)

  def destroy(self, request, *args, **kwargs):
    instance = self.get_object()
    if instance.author != self.request.user:
      data = {
        'validation_err' : '작성자 본인만 삭제할 수 있습니다.'
      }
      return Response(data=data, status=status.HTTP_401_UNAUTHORIZED)
    self.perform_destroy(instance)
    return Response(status=status.HTTP_204_NO_CONTENT)


# Answer Detail & Delete
class AnswerDetailDeleteAPIView(RetrieveDestroyAPIView):
  queryset = Answer.objects.all()
  serializer_class = AnswerDeleteSerializer

  # retrieve
  def get(self, request, *args, **kwargs):
    return self.retrieve(request, *args, **kwargs)

  def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    if instance.author != self.request.user:
      data = {
        'validation_err' : '작성자 본인만 조회할 수 있습니다.'
      }
      return Response(data=data, status=status.HTTP_401_UNAUTHORIZED)
    serializer = self.get_serializer(instance)
    return Response(serializer.data)

  # destroy
  def delete(self, request, *args, **kwargs):
    return self.destroy(request, *args, **kwargs)

  def destroy(self, request, *args, **kwargs):
    instance = self.get_object()
    if instance.author != self.request.user:
      data = {
        'validation_err' : '작성자 본인만 삭제할 수 있습니다.'
      }
      return Response(data=data, status=status.HTTP_401_UNAUTHORIZED)
    self.perform_destroy(instance)
    return Response(status=status.HTTP_204_NO_CONTENT)
