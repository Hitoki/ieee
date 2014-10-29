from rest_framework import serializers
from webapp.models import ConferenceApplication, TagKeyword


class ConferenceApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConferenceApplication
        fields = ('id', 'name', 'keywords', )
        depth = 1


class TagKeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TagKeyword
        fields = ('id', 'name', 'tag', )
