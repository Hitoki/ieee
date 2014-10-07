from django import template

register = template.Library()

@register.inclusion_tag('site_admin/manage_society_tags_table.html', takes_context=True)
def manage_society_tags_table(context):
    'Includes the /site_admin/manage_society_tags_table.html template.'
    return context
