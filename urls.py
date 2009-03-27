from django.conf.urls.defaults import *
import django.contrib.admin
import os.path

import site_admin.views
import settings
import views

django.contrib.admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', views.index, name='index'),
    url(r'^roamer$', views.roamer, name='roamer'),
    url(r'^textui$', views.textui, name='textui'),
    url(r'^feedback$', views.feedback, name='feedback'),
    url(r'^browser_warning$', views.browser_warning, name='browser_warning'),
    
    url(r'^ajax/tag_content$', views.ajax_tag_content, name='ajax_tag_content'),
    url(r'^ajax/node$', views.ajax_node, name='ajax_node'),
    url(r'^ajax/nodes_xml$', views.ajax_nodes_xml, name='ajax_nodes_xml'),
    url(r'^ajax/nodes_json$', views.ajax_nodes_json, name='ajax_nodes_json'),
    url(r'^ajax/tooltip$', views.tooltip, name='tooltip'),
    
    url(r'^ajax/search_tags$', views.ajax_search_tags, name='search_tags'),
    url(r'^ajax/search_resources$', views.ajax_search_resources, name='search_resources'),
    url(r'^ajax/search_societies$', views.ajax_search_societies, name='search_societies'),
    url(r'^ajax/update_society$', views.ajax_update_society, name='ajax_update_society'),
    
    # Site Admin
    (r'^admin/', include('ieeetags.site_admin.urls')),
    
    # Django Admin
    url(r'^djangoadmin/(.*)', django.contrib.admin.site.root, name='admin'),
    
    # Cached media static serving
    (r'^%s(?P<path>.*)$' % settings.CACHED_MEDIA_URL.lstrip('/'), 'django.views.static.serve', {'document_root': settings.CACHED_MEDIA_ROOT}),
    
    # Media
    url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
     
)
