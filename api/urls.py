from django.conf.urls import patterns, include, url
from api.views import ConferenceApplicationDetail, ConferenceApplicationList, \
    TagKeywordList, TagKeywordDetail, ConferenceApplicationFilteredList, \
    NodesSearchList


urlpatterns = patterns(
    '',

    url(r'^conference-applications/?$',
        ConferenceApplicationList.as_view(),
        name='api-conference-applications'),

    url(r'^conference-applications/(?P<pk>[-\w]+)/?$',
        ConferenceApplicationDetail.as_view(),
        name='api-conference-application'),

    url(r'^conference-applications/filter/(?P<keyword_name>.+)/?$',
        ConferenceApplicationFilteredList.as_view(),
        name='api-conference-applications'),

    url(r'^tag-keywords/?$',
        TagKeywordList.as_view(),
        name='api-tag-keywords'),

    url(r'^tag-keywords/(?P<pk>[\w-]+)/?$',
        TagKeywordDetail.as_view(),
        name='api-tag-keyword'),

    url(r'^nodes/search/?$',
        NodesSearchList.as_view(),
        name='nodes-search'),
)
