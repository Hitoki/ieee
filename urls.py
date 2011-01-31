from django.conf.urls.defaults import *
import django.contrib.admin
import os.path

import site_admin.views
import settings
import views

django.contrib.admin.autodiscover()

if not settings.DEBUG:
    # Set the custom error handler for production servers
    handler500 = 'ieeetags.views.error_view'

if settings.DISABLE_SITE:
    # Disable the entire site!
    urlpatterns = patterns('',
        url(r'^.*$', views.site_disabled, name='site_disabled'),
    )
    
else:
    urlpatterns = patterns('',
        url(r'^$', views.index, name='index'),
        url(r'^roamer$', views.roamer, name='roamer'),
        url(r'^textui/(survey)?$', views.textui, name='textui'),
        url(r'^textui_help$', views.textui_help, name='textui_help'),
        url(r'^textui_home$', views.textui_home, name='textui_home'),
        url(r'^feedback$', views.feedback, name='feedback'),
        url(r'^browser_warning$', views.browser_warning, name='browser_warning'),
        url(r'^xplore_full_results/(?P<tag_id>\d+)$', views.xplore_full_results, name='xplore_full_results'),
        url(r'^tester_message$', views.tester_message, name='tester_message'),
        
        # AJAX
        #url(r'^ajax/tag_content$', views.ajax_tag_content, name='ajax_tag_content'),
        url(r'^ajax/tag_content/(?P<tag_id>\d+)/(?P<ui>\S+)$', views.ajax_tag_content, name='ajax_tag_content'),
        url(r'^ajax/tag_content/(?P<tag_slug>\d+)/(?P<ui>\S+)$', views.ajax_tag_content, name='ajax_tag_content'),
        #url(r'^ajax/term_content/(?P<term_id>\d+)/(?P<ui>\S+)$', views.ajax_term_content, name='ajax_term_content'),
        url(r'^ajax/xplore_results$', views.ajax_xplore_results, name='ajax_xplore_results'),
        url(r'^ajax/node$', views.ajax_node, name='ajax_node'),
        url(r'^ajax/nodes_xml$', views.ajax_nodes_xml, name='ajax_nodes_xml'),
        url(r'^ajax/textui_nodes$', views.ajax_textui_nodes, name='ajax_textui_nodes'),
        url(r'^ajax/tooltip/(?P<tag_id>\d+)$', views.tooltip, name='tooltip'),
        url(r'^ajax/tooltip$', views.tooltip, name='tooltip'),
        url(r'^ajax/video$', views.ajax_video, name='ajax_video'),
        
        url(r'^ajax/profile_log$', views.ajax_profile_log, name='ajax_profile_log'),
        
        # Print
        url(r'^print/resource/(?P<tag_id>\d+)/(?P<resource_type>.+)$', views.print_resource, name='print_resource'),
        
        # Tag
        url(r'^tags/', views.tags_list, name='tags_list'),
        url(r'^tag/(?P<tag_id>\d+)/[0-9a-zA-Z_-]*$', views.tag_landing, name='tag_landing'),
        
        # Single static SWF file, for Flash player bug
        url(r'^admin/(?P<path>SkinUnderAllNoCaption.swf)$', 'django.views.static.serve', {'document_root': '%s/flash' % settings.MEDIA_ROOT}),
        
        # Site Admin
        (r'^admin/', include('ieeetags.site_admin.urls')),
        
        # Django Admin
        url(r'^djangoadmin/(.*)', django.contrib.admin.site.root, name='admin'),
        
        # Cached media static serving
        (r'^%s(?P<path>.*)$' % settings.CACHED_MEDIA_URL.lstrip('/'), 'django.views.static.serve', {'document_root': settings.CACHED_MEDIA_ROOT}),
        
        # Media
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        
        # Debug
        url(r'^debug/error$', views.debug_error, name='debug_error'),
        url(r'^debug/send_email$', views.debug_send_email, name='debug_send_email'),
    )

if settings.DEBUG:
    # Test views
    urlpatterns += patterns('',
        url(r'^test/error$', views.test_error, name='test_error'),
        url(r'^test/lightbox_error$', views.test_lightbox_error, name='test_lightbox_error'),
        url(r'^test/browsers$', views.test_browsers, name='test_browsers'),
    )