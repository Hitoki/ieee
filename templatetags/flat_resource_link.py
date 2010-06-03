#!/usr/bin/env python
# encoding: utf-8
"""
flat_resource_link.py

Template tag for generating a resource name with no link (for printing, etc) or linked (for tag landing pages)

"""

from django import template

register = template.Library()

@register.tag('flat_resource_link')
def flat_resource_link(parser, token):
    tag_name, node_id, node_text = token.split_contents()
    return FlatResourceLinkNode(node_id, node_text)

class FlatResourceLinkNode(template.Node):
    
    def __init__(self, node_id, node_text):
        self.node_id = template.Variable(node_id)
        self.node_text = template.Variable(node_text)
    
    def render(self, context):

        if context["create_links"]:
            return '<a href="/tag/%d">%s</a>' % (int(self.node_id.resolve(context)), self.node_text.resolve(context))
        else:
            return self.node_text.resolve(context)
