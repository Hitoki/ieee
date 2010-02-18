from django.conf.urls.defaults import *

import views

urlpatterns = patterns('',
    
    url(r'^login$', views.login, name='admin_login'),
    url(r'^logout$', views.logout, name='admin_logout'),
    url(r'^forgot_password$', views.forgot_password, name='forgot_password'),
    url(r'^forgot_password_confirmation$', views.forgot_password_confirmation, name='forgot_password_confirmation'),
    url(r'^password_reset/(?P<user_id>\d+)/(?P<reset_key>.+)$', views.password_reset, name='password_reset'),
    url(r'^password_reset_success$', views.password_reset_success, name='password_reset_success'),
    url(r'^change_password$', views.change_password, name='change_password'),
    url(r'^change_password_success$', views.change_password_success, name='change_password_success'),
    
    url(r'^$', views.home, name='admin_home'),
    #url(r'^home_societies_list$', views.home_societies_list, name='admin_home_societies_list'),
    url(r'^missing_resource/(?P<society_id>\d+)$', views.missing_resource, name='missing_resource'),
    url(r'^permission_denied$', views.permission_denied, name='permission_denied'),
    
    #url(r'^unassigned_tags$', views.unassigned_tags, name='admin_unassigned_tags'),
    #url(r'^fix_societies_import$', views.fix_societies_import, name='admin_fix_societies_import'),
    url(r'^import_societies$', views.import_societies, name='admin_import_societies'),
    #url(r'^import_societies_and_tags$', views.import_societies_and_tags, name='admin_import_societies_and_tags'),
    #url(r'^import_conferences/(?P<source>.+)$', views.import_conferences, name='admin_import_conferences'),
    #url(r'^import_periodicals/(?P<source>.+)$', views.import_periodicals, name='admin_import_periodicals'),
    #url(r'^import_standards/(?P<source>.+)$', views.import_standards, name='admin_import_standards'),
    #url(r'^fix_user_import$', views.fix_user_import, name='admin_fix_user_import'),
    url(r'^users/import$', views.import_users, name='admin_import_users'),
    url(r'^import_resources$', views.import_resources, name='admin_import_resources'),
    url(r'^import/clusters$', views.import_clusters, name='admin_import_clusters'),
    url(r'^import/conference_series$', views.import_conference_series, name='admin_import_conference_series'),
    
    url(r'^sectors$', views.list_sectors, name='admin_list_sectors'),
    url(r'^sector/(\d+)$', views.view_sector, name='admin_view_sector'),
    
    url(r'^list_orphan_tags$', views.list_orphan_tags, name='admin_list_orphan_tags'),
    url(r'^send_email_all_users$', views.send_email_all_users, name='admin_send_email_all_users'),
    url(r'^send_email_all_users_confirmation$', views.send_email_all_users_confirmation, name='admin_send_email_all_users_confirmation'),
    
    # Tags
    url(r'^tags/edit$', views.edit_tags, name='admin_edit_tags'),
    url(r'^tags$', views.list_tags, name='admin_list_tags'),
    url(r'^tag/(\d+)$', views.view_tag, name='admin_view_tag'),
    url(r'^tag/create$', views.create_tag, name='admin_create_tag'),
    url(r'^tag/(?P<tag_id>\d+)/edit$', views.edit_tag, name='admin_edit_tag'),
    url(r'^tags/search$', views.search_tags, name='admin_search_tags'),
    url(r'^tag/(?P<tag_id>\d+)/save$', views.save_tag, name='admin_save_tag'),
    url(r'^tag/(?P<tag_id>\d+)/delete$', views.delete_tag, name='admin_delete_tag'),
    #url(r'^tags/combine/(?P<tag_id1>\d+)/(?P<tag_id2>\d+)$', views.combine_tags, name='admin_combine_tags'),
    url(r'^tags/combine$', views.combine_tags, name='admin_combine_tags'),
    
    # Clusters
    url(r'^cluster/(?P<cluster_id>\d+)$', views.view_cluster, name='admin_view_cluster'),
    url(r'^cluster/(?P<cluster_id>\d+)/edit$', views.edit_cluster, name='admin_edit_cluster'),
    url(r'^cluster/create$', views.edit_cluster, name='admin_create_cluster'),
    url(r'^cluster/(?P<cluster_id>\d+)/delete$', views.delete_cluster, name='admin_delete_cluster'),
    
    # Users
    url(r'^users$', views.users, name='admin_users'),
    url(r'^user/(?P<user_id>\d+)$', views.view_user, name='admin_view_user'),
    url(r'^user/create$', views.edit_user, name='admin_create_user'),
    url(r'^user/(?P<user_id>\d+)/edit$', views.edit_user, name='admin_edit_user'),
    url(r'^user/save$', views.save_user, name='admin_save_user'),
    url(r'^user/(?P<user_id>\d+)/delete$', views.delete_user, name='admin_delete_user'),
    url(r'^users/delete$', views.delete_users, name='admin_delete_users'),
    url(r'^users/send_login_info/(?P<reason>.+)$', views.send_login_info, name='admin_send_login_info'),
    
    # Societies
    url(r'^societies$', views.societies, name='admin_societies'),
    url(r'^society/(?P<society_id>\d+)$', views.view_society, name='admin_view_society'),
    url(r'^society/(?P<society_id>\d+)/manage$', views.manage_society, name='admin_manage_society'),
    url(r'^society/(?P<society_id>\d+)/manage/tags_table/(?P<tag_sort>.+)/(?P<tag_page>.+)/(?P<items_per_page>.+)$', views.manage_society_tags_table, name='admin_manage_society_tags_table'),
    #url(r'^society/create$', views.edit_society, name='admin_create_society'),
    url(r'^society/(?P<society_id>\d+)/edit$', views.edit_society, name='admin_edit_society'),
    url(r'^society/save$', views.save_society, name='admin_save_society'),
    url(r'^society/(?P<society_id>\d+)/delete$', views.delete_society, name='admin_delete_society'),
    url(r'^societies/search$', views.search_societies, name='admin_search_societies'),
    
    # Resources
    url(r'^resources/edit$', views.edit_resources, name='admin_edit_resources'),
    url(r'^resources/search$', views.search_resources, name='admin_search_resources'),
    url(r'^resource/(?P<resource_id>\d+)$', views.view_resource, name='admin_view_resource'),
    url(r'^resource/(?P<resource_id>\d+)/edit$', views.edit_resource, name='admin_edit_resource'),
    url(r'^resource/create$', views.edit_resource, name='admin_create_resource'),
    url(r'^resource/save$', views.save_resource, name='admin_save_resource'),
    url(r'^resource/(?P<resource_id>\d+)/delete$', views.delete_resource, name='admin_delete_resource'),
    #url(r'^resources/remove_priorities$', views.remove_priorities, name='admin_remove_priorities'),
    url(r'^resources/(?P<type1>.+)$', views.list_resources, name='admin_list_resources'),
    
    url(r'^resource/(?P<resource_id>\d+)/paste$', views.paste_resource, name='admin_paste_resource'),
    
    # AJAX
    url(r'^ajax/search_tags$', views.ajax_search_tags, name='ajax_search_tags'),
    url(r'^ajax/search_resources$', views.ajax_search_resources, name='ajax_search_resources'),
    url(r'^ajax/search_societies$', views.ajax_search_societies, name='ajax_search_societies'),
    url(r'^ajax/update_society$', views.ajax_update_society, name='ajax_update_society'),
    url(r'^ajax/copy_resource_tags$', views.ajax_copy_resource_tags, name='ajax_copy_resource_tags'),
    url(r'^ajax/paste_resource_tags$', views.ajax_paste_resource_tags, name='ajax_paste_resource_tags'),
    
    # Reports
    url(r'^report/login$', views.login_report, name='admin_login_report'),
    url(r'^report/tagged_resources/(?P<filter>.+)$', views.tagged_resources_report, name='admin_tagged_resources_report'),
    url(r'^report/tags_report$', views.tags_report, name='admin_tags_report'),
    url(r'^report/clusters$', views.clusters_report, name='admin_clusters_report'),
    url(r'^report/priority$', views.priority_report, name='admin_priority_report'),
    url(r'^report/duplicate_tags$', views.duplicate_tags_report, name='admin_duplicate_tags_report'),
    url(r'^report/society_logos$', views.society_logos_report, name='admin_society_logos_report'),
    url(r'^report/conference_series$', views.conference_series_report, name='admin_conference_series_report'),
    url(r'^report/broken_links$', views.broken_links_report, name='admin_broken_links_report'),
    url(r'^report/broken_links/reset/(?P<reset_type>.+)/(?P<resource_id>\d+)$', views.broken_links_reset, name='admin_broken_links_reset'),
    url(r'^report/broken_links/reset/(?P<reset_type>.+)$', views.broken_links_reset, name='admin_broken_links_reset'),
    url(r'^report/broken_links/check/(?P<check_type>.+)/(?P<resource_id>\d+)$', views.broken_links_check, name='admin_broken_links_check'),
    url(r'^report/broken_links/check$', views.broken_links_check, name='admin_broken_links_check'),
    url(r'^report/broken_links/cancel$', views.broken_links_cancel, name='admin_broken_links_cancel'),
    url(r'^create_fake_tags$', views.create_fake_tags, name='admin_create_fake_tags'),
    url(r'^live_search/results$', views.live_search_results, name='admin_live_search_results'),
    
    # Exports
    url(r'^export/tab_resources$', views.export_tab_resources, name='admin_export_tab_resources'),
    
    # Server Admin
    #url(r'^server/update_svn$', views.server_update_svn, name='admin_server_update_svn'),
    
    # DEBUG:
    #url(r'^DEBUG_CREATE_ADMIN$', views.create_admin_login, name='create_admin_login'),
    url(r'^info$', views.admin_info, name='admin_info'),
)
