from rest_framework import viewsets
from api.serializers import ConferenceApplicationSerializer, \
    TagKeywordSerializer
from webapp.models import ConferenceApplication, TagKeyword


class ConferenceApplicationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class TagKeywordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer
