from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from api.serializers import ConferenceApplicationSerializer, \
    TagKeywordSerializer, NodeSerializer
from webapp.models import ConferenceApplication, TagKeyword
from webapp.views import get_nodes


class ConferenceApplicationList(generics.ListAPIView):
    """
    API endpoint that returns a list of all conference applications
    """
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class ConferenceApplicationFilteredList(APIView):
    """
    API endpoint that returns a list of conference applications filtered by \
    tag keyword
    """
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
    """
    API endpoint that returns details for one conference application
    """
    queryset = ConferenceApplication.objects.all()
    serializer_class = ConferenceApplicationSerializer


class TagKeywordList(generics.ListAPIView):
    """
    API endpoint that returns a list of all tag keywords
    """
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer


class TagKeywordDetail(generics.RetrieveAPIView):
    """
    API endpoint that returns details for one tag keyword
    """
    queryset = TagKeyword.objects.all()
    serializer_class = TagKeywordSerializer


class NodesSearchList(APIView):
    """
    API endpoint that returns search results for the nodes
    """
    def get(self, request, format=None):
        if not 's' in request.GET or not len(request.GET['s'].strip()):
            return Response({'error': 'no search term provided'})
        nodes = get_nodes(request.GET['s'])
        serializer = NodeSerializer(nodes, many=True)
        return Response(serializer.data)
