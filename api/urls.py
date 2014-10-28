from django.conf.urls import patterns, include, url
from api.views import ConferenceApplicationDetail, ConferenceApplicationList, \
    TagKeywordList, TagKeywordDetail


urlpatterns = patterns(
    '',

    url(r'^conference-applications/?$',
        ConferenceApplicationList.as_view(),
        name='api-conference-applications'),

    url(r'^conference-applications/(?P<pk>[\w-]+)/?$',
        ConferenceApplicationDetail.as_view(),
        name='api-conference-application'),

    url(r'^tag-keywords/?$',
        TagKeywordList.as_view(),
        name='api-tag-keywords'),

    url(r'^tag-keywords/(?P<pk>[\w-]+)/?$',
        TagKeywordDetail.as_view(),
        name='api-tag-keyword'),
)
