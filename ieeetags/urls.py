from django.conf.urls import *
import django.contrib.admin
import os.path
from django.shortcuts import render as django_render

import site_admin.views
from django.conf import settings
from webapp.views import *

from sitemaps import *

django.contrib.admin.autodiscover()


if not settings.DEBUG:
    # Set the custom error handler for production servers
    handler500 = 'ieeetags.views.views.error_view'

if settings.DISABLE_SITE:
    # Disable the entire site!
    urlpatterns = patterns('',
        url(r'^.*$', views.site_disabled, name='site_disabled'),
    )
    
else:
    urlpatterns = patterns('',
        url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap',
            {'sitemaps': {
                    'OneOffs':        OneOffsSitemap
                    ,'TagsStartWith': TagsStartWithSitemap
                    ,'Tags':          TagLandingSitemap
                    }
             }
        ),
        url(r'^$', views.index, name='index'),
        url(r'^roamer$', views.roamer, name='roamer'),
        url(r'^textui/(survey)?$', views.textui, name='textui'),
        url(r'^textui_new$', views.textui, name='textui_new'),
        url(r'^textui_help$', views.textui_help, name='textui_help'),
        url(r'^textui_home$', views.textui_home, name='textui_home'),
        url(r'^feedback$', views.feedback, name='feedback'),
        url(r'^browser_warning$', views.browser_warning, name='browser_warning'),
        url(r'^xplore_full_results/(?P<tag_id>\d+)$', xplore.xplore_full_results, name='xplore_full_results'),
        # AJAX
        #url(r'^ajax/tag_content$', views.ajax_tag_content, name='ajax_tag_content'),
        url(r'^ajax/tag_content/(?P<tag_id>\d+)/(?P<ui>\S+)/(?P<tab>\S+)$', ajax.ajax_tag_content, name='ajax_tag_content'),
        url(r'^ajax/tag_content/(?P<tag_slug>\d+)/(?P<ui>\S+/(?P<tab>\S+))$', ajax.ajax_tag_content, name='ajax_tag_content'),
        #url(r'^ajax/term_content/(?P<term_id>\d+)/(?P<ui>\S+)$', views.ajax_term_content, name='ajax_term_content'),
        url(r'^ajax/xplore_results$', xplore.ajax_xplore_results, name='ajax_xplore_results'),
        url(r'^ajax/recent_xplore$', xplore.ajax_recent_xplore, name='ajax_recent_xplore'),
        url(r'^ajax/jobs_results$', ajax.ajax_jobs_results, name='ajax_jobs_results'),
        url(r'^ajax/authors_results$', ajax.ajax_authors_results, name='ajax_authors_results'),
        url(r'^ajax/tv_results$', ajax.ajax_tv_results, name='ajax_tv_results'),
        url(r'^ajax/node$', ajax.ajax_node, name='ajax_node'),
        url(r'^ajax/nodes_xml$', ajax.ajax_nodes_xml, name='ajax_nodes_xml'),
        url(r'^ajax/nodes_json$', ajax.ajax_nodes_json, name='ajax_nodes_json'),
        url(r'^ajax/nodes_keywords$', ajax.ajax_nodes_keywords, name='ajax_nodes_keywords'),
        url(r'^ajax/textui_nodes$', ajax.ajax_textui_nodes, name='ajax_textui_nodes'),
        url(r'^ajax/tooltip/(?P<tag_id>\d+)$', ajax.tooltip, name='tooltip'),
        url(r'^ajax/tooltip$', ajax.tooltip, name='tooltip'),
        url(r'^ajax/video$', ajax.ajax_video, name='ajax_video'),
        url(r'^ajax/welcome$', ajax.ajax_welcome, name='ajax_welcome'),
        url(r'^ajax/profile_log$', ajax.ajax_profile_log, name='ajax_profile_log'),
        url(r'^ajax/notification/request$', ajax.ajax_notification_request),
        
        url(r'^ajax/javascript_error_log$', ajax.ajax_javascript_error_log, name='ajax_javascript_error_log'),
        
        # Print
        url(r'^print/resource/(?P<tag_id>\d+)/(?P<resource_type>.+)$', views.print_resource, name='print_resource'),
        
        # SEO-style pages
        url(r'^tags/?$', views.tags_list, name='tags_list'),
        url(r'^tags/starts/(?P<starts_with>.+)/?$', views.tags_starts, name='tags_starts'),
        url(r'^tags/all/?$', views.tags_all,name='tags_all'),
        url(r'^tag/(?P<tag_id>\d+)/[0-9a-zA-Z_-]*/?$', views.tag_landing, name='tag_landing'),
        url(r'^clusters/', views.clusters_list, name='clusters_list'),
        url(r'^cluster/(?P<cluster_id>\d+)/[0-9a-zA-Z_-]*/?$', views.cluster_landing, name='cluster_landing'),
        
        # Single static SWF file, for Flash player bug
        url(r'^admin/(?P<path>SkinUnderAllNoCaption.swf)$', 'django.views.static.serve', {'document_root': '%s/flash' % settings.MEDIA_ROOT}),
        
        # Site Admin
        (r'^admin/', include('site_admin.urls')),
        
        # Django Admin
        #url(r'^djangoadmin/(.*)', django.contrib.admin.site.root, name='admin'),
        
        # Cached media static serving
        (r'^%s(?P<path>.*)$' % settings.CACHED_MEDIA_URL.lstrip('/'), 'django.views.static.serve', {'document_root': settings.CACHED_MEDIA_ROOT}),
        
        # Media
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        
        # Faux page for demo
        (r'^scss/$', django_render, {'template': 'scss.html'}),
    )

if settings.DEBUG:
    # Test views.views
    urlpatterns += patterns('',
        url(r'^test/error$', views.test_error, name='test_error'),
        url(r'^test/lightbox_error$', views.test_lightbox_error, name='test_lightbox_error'),
        url(r'^test/browsers$', views.test_browsers, name='test_browsers'),

        # Debug
        url(r'^debug/error$',
            views.debug_error,
            name='debug_error'),

        url(r'^debug/send_email$',
            views.debug_send_email,
            name='debug_send_email'),

        url(r'^debug/conf_app/create/random$',
            views.debug_conf_app_create,
            name='debug_conf_app_create'),

        url(r'^debug/conf_app/by_keyword/(?P<keyword_name>.*)$',
            views.debug_conf_apps_by_keyword,
            name='debug_conf_apps_by_keyword'),

        url(r'^debug/conf_app/list$',
            ConferenceApplicationListView.as_view(),
            name='conference_applications'),

        url(r'^debug/conf_app/create$',
            ConferenceApplicationCreateView.as_view(),
            name='create_conference_application'),

    )
