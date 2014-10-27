from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from rest_framework import routers
from api.views import ConferenceApplicationViewSet, TagKeywordViewSet


router = routers.DefaultRouter()
router.register(r'conference_applications', ConferenceApplicationViewSet)
router.register(r'tag-keywords', TagKeywordViewSet)


urlpatterns = patterns(
    '',

    url(r'', include(router.urls)),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
