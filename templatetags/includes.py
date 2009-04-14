from django import template

register = template.Library()

@register.inclusion_tag('site_admin/manage_society_tags_table.html', takes_context=True)
def manage_society_tags_table(context):
    return context
