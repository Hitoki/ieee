from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from api.serializers import ConferenceApplicationSerializer, \
    TagKeywordSerializer
from webapp.models import ConferenceApplication, TagKeyword


class ConferenceApplicationList(generics.ListCreateAPIView):
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class ConferenceApplicationFilteredList(APIView):
    def get_objects(self, keyword_name):
        try:
            keyword = TagKeyword.objects.get(name=keyword_name)
            return keyword.conference_applications.all()
        except TagKeyword.DoesNotExist:
            raise Http404

    def get(self, request, keyword_name, format=None):
        objects = self.get_objects(keyword_name)
        serializer = ConferenceApplicationSerializer(objects, many=True)
        return Response(serializer.data)


class ConferenceApplicationDetail(generics.RetrieveAPIView):
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class TagKeywordList(generics.ListCreateAPIView):
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer


class TagKeywordDetail(generics.RetrieveAPIView):
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer
