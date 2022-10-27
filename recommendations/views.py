from django.shortcuts import render
from .models import Recommendation
from .serializers import RecommendationDetailSerializer, RecommendationListSerializer, RecommendationSerializer
from .permissions import IsOwnerCheck
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, RetrieveDestroyAPIView
from datetime import datetime

# Create your views here.
TYPE_MAPPER = ['과일', '채소', '콩/두부', '통곡물', '버섯', '해조류', '견과', '고기/생선/달걀', '유제품', '가공 식품', '영양제', '주의']

# GET api 두 개 필요
# 1) 사용자 GET : self.request.user과 쿼리 파라미터 date 사용 - LIST / RETRIEVE
class RecommendationUserListView(APIView):
  def get(self, request):
    user = request.user.username
    recommendations = Recommendation.objects.filter(target=user).order_by('-created_at')
    # 해당 쿼리를 serializer에 넣어서 id, target, title(?), created_at, start_date만 내려주도록 변경
    serializer = RecommendationListSerializer(instance=recommendations, many=True)
    return Response(data=serializer.data)


class RecommendationUserDetailView(RetrieveAPIView):
  queryset = Recommendation.objects.all()
  serializer_class = RecommendationDetailSerializer

  def get_permissions(self):
    permission_classes = [IsOwnerCheck]
    return [permission() for permission in permission_classes]

  def get(self, request, *args, **kwargs):
    return self.retrieve(request, *args, **kwargs)

  def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    data = []
    for i in range(12):
      # print(recommendation[0][f'type{i+1}'])
      # type_num = f'type{i+1}'
      temp_list = instance.get_type(i+1).split('|')  #어떻게 처리해야 할지 모르겟음 ㅠㅠ
      # print(temp_list)
      temp_data = {
        'type' : TYPE_MAPPER[i],
        'main' : temp_list[0],
        'list' : temp_list[1:-1],
        'order' : int(temp_list[-1])
      }
      # print(temp_data)
      if temp_list[-1] == "-1": # -1인 데이터 제거
        continue
      data.append(temp_data)
    # data 결과 ordering으로 정렬
    data = sorted(data, key=lambda x: x['order'])
    result = {
      'data' : data,
      'comment' : instance.comment,
      'hashtag' : instance.hashtag
    }
    return Response(data=result)
    # serializer = self.get_serializer(data, many=True)
    # return Response(serializer.data)

# class RecommendationUserDetailView(APIView):

#   # permission_classes = [IsOwner]
#   def get_permissions(self):
#     permission_classes = [IsOwnerCheck]
#     # permission_classes = [IsAdminUser]
#     return [permission() for permission in permission_classes]

#   def get(self, request, pk): # 이렇게만 해도 pk값 넘어옴
#     recommendation = Recommendation.objects.filter(pk=pk).values()
#     if recommendation.exists():
#       data = []
#       for i in range(11):
#         # print(recommendation[0][f'type{i+1}'])
#         temp_list = recommendation[0][f'type{i+1}'].split('|')
#         # print(temp_list)
#         temp_data = {
#           'type' : TYPE_MAPPER[i],
#           'main' : temp_list[0],
#           'list' : temp_list[1:]
#         }
#         # print(temp_data)
#         data.append(temp_data)
#       serializer = RecommendationDetailSerializer(instance=data, many=True)
#       return Response(data=serializer.data)
#     else:
#       data = {
#         'err_msg' : 'pk값이 존재하지 않습니다.'
#       }
#       return Response(data=data, status=status.HTTP_400_BAD_REQUEST)


# 2) 연구원 GET : 쿼리 파라미터 user과 date 사용
# POST / PATCH / DELETE 메서드 구현 필요

# 연구원 GET / POST api
class RecommendationAdminCreateView(APIView):
  
  def get(self, request):
    date = self.request.GET.get('date', None)
    # 예외처리
    if date is None:
      data = {
        'err_msg' : '날짜를 입력해주세요'
      }
      return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    date_data = datetime.fromtimestamp(int(date)/1000)
    user = self.request.GET.get('user', None)
    recommendation = Recommendation.objects.filter(target=user, created_at=date_data).values()
    # 예외처리
    if not recommendation.exists():
      data = {
        'err_msg' : '해당 날짜에 입력한 데이터가 없습니다.'
      }
      return Response(data=data, status=status.HTTP_400_BAD_REQUEST)
    else:
      result  = {}
      data = []
      for i in range(12):
        # print(recommendation[0][f'type{i+1}'])
        temp_list = recommendation[0][f'type{i+1}'].split('|')
        # 주의 추가 **
        temp_data = {
          'type' : TYPE_MAPPER[i],
          'main' : temp_list[0],
          'list' : temp_list[1:-1],
          'order' : int(temp_list[-1])
        }
        # print(temp_data)
        data.append(temp_data)
      # PATCH / DELETE에 사용하기 위한 ID 값 추가
      result = {
        'data' : data,
        'comment' : recommendation[0]['comment'], # 코멘트 추가
        'hashtag' : recommendation[0]['hashtag'], # 해시태그 추가
        'id' : recommendation[0]['id']
      }
      return Response(data=result)

  def post(self, request):
    # print(request.data)
    # request.data 가공 필요
    date_data = datetime.fromtimestamp(int(request.data['created_at'])/1000)
    data =  {
      'target' : request.data['target'],
      'created_at' : date_data,
      'comment' : request.data['comment'], # 코멘트 추가
      'hashtag' : request.data['hashtag'] # 해시태그 추가(없으면 빈 스트링으로라도 입력받아야 함)
    }
    # print(data)

    recommendations = request.data['data']
    # print(recommendations)
    # QA 필요!!!
    for i in range(12):
      result = ''
      result += recommendations[i]['main'] 
      for elem in recommendations[i]['list']:
        result = result + '|' + elem
      # 주의 추가 **
      result = result + '|' + str(recommendations[i]['order'])
      data[f'type{i+1}'] = result

    # print(data)
    serializer = RecommendationSerializer(data=data)
    if serializer.is_valid():
      serializer.save()
      return Response(data=serializer.data)
    else:
      return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# 연구원 UPDATE DELETE api (PATCH/DELETE)
class RecommendationAdminUpdateView(RetrieveUpdateDestroyAPIView):
  queryset = Recommendation.objects.all()
  serializer_class = RecommendationDetailSerializer
  
  # GET
  def get(self, request, *args, **kwargs):
    return self.retrieve(request, *args, **kwargs)

  def retrieve(self, request, *args, **kwargs):
    instance = self.get_object()
    data = []
    for i in range(12):
      # print(recommendation[0][f'type{i+1}'])
      # type_num = f'type{i+1}'
      temp_list = instance.get_type(i+1).split('|')  #어떻게 처리해야 할지 모르겟음 ㅠㅠ
      # print(temp_list)
      temp_data = {
        'type' : TYPE_MAPPER[i],
        'main' : temp_list[0],
        'list' : temp_list[1:-1],
        'order' : int(temp_list[-1])
      }
      # print(temp_data)
      data.append(temp_data)
    result = {
      'data' : data,
      'comment' : instance.comment,
      'hashtag' : instance.hashtag
    }
    return Response(data=result)
    # serializer = self.get_serializer(data, many=True)
    # return Response(serializer.data)

  # PATCH (내부적으로는 UPDATE로 동작)
  def patch(self, request, *args, **kwargs):
    return self.partial_update(request, *args, **kwargs)

  def update(self, request, *args, **kwargs):
      partial = kwargs.pop('partial', False)
      instance = self.get_object()
      # print(request.data)
      # request data를 RECOMMENDATION 모델에 맞게 수정 후 대입 **
      data = {}
      recommendations = request.data['data']
      # print(recommendations)
      # QA 필요!!!
      for i in range(12):
        result = ''
        result += recommendations[i]['main'] # 한 개 반드시 필요가 아니라 없을 수도... 없는 경우 예외처리 필요? 빈리스트로 들어오면 에러가 안뜰수도..!
        for elem in recommendations[i]['list']: # 개수만큼 돌기 때문에 없는 경우 저장 안 될듯?
          result = result + '|' + elem
        # 주의 추가 **
        result = result + '|' + str(recommendations[i]['order'])
        data[f'type{i+1}'] = result
      # 코멘트 추가 **
      data['comment'] = request.data['comment']
      # 해시태그 추가
      data['hashtag'] = request.data['hashtag']
      serializer = RecommendationSerializer(instance, data=data, partial=partial)
      # serializer = self.get_serializer(instance, data=request.data, partial=partial)
      serializer.is_valid(raise_exception=True)
      self.perform_update(serializer)

      if getattr(instance, '_prefetched_objects_cache', None):
          # If 'prefetch_related' has been applied to a queryset, we need to
          # forcibly invalidate the prefetch cache on the instance.
          instance._prefetched_objects_cache = {}

      # serializer간 충돌이 발생하므로 마지막 list 필드에 수정된 결과를 (야매로) JSON 형식으로 담아서 response 내려줌 **
      data = {
        'type' : '',
        'main' : '',
        'list' : serializer.data,
        'order' : ''
      }
      # return Response(serializer.data)
      return Response(data=data)

  def perform_update(self, serializer):
      serializer.save()

  def partial_update(self, request, *args, **kwargs):
      kwargs['partial'] = True
      return self.update(request, *args, **kwargs)
