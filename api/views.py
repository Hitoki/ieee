from rest_framework import generics
from api.serializers import ConferenceApplicationSerializer, \
    TagKeywordSerializer
from webapp.models import ConferenceApplication, TagKeyword


class ConferenceApplicationList(generics.ListAPIView):
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class ConferenceApplicationDetail(generics.RetrieveAPIView):
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class TagKeywordList(generics.ListAPIView):
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer


class TagKeywordDetail(generics.RetrieveAPIView):
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer
