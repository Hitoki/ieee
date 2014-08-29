from django import template


register = template.Library()


def _strip_quotes(str):
    import re
    matches = re.match(r'("|\')(.+)("|\')', str)
    if matches is None:
        raise Exception('Parameter %s is not in single or double quotes '
                        '(ie. "%s" or \'%s\'' % (str, str, str))
    return matches.group(2)


@register.tag
def ifpermission(parser, token):
    """
    Usage:
      {% ifpermission [permission_type] [object] %}
        content
      {% else %}
        content
      {% endifpermission %}

    Calls the Permission.objects.[permission_type]() function with the current
    user and the given object.  If true, renders the contents of this tag.
    If false, renders nothing.
    """
    tokens = token.split_contents()
    tag_name, permission_type, object = tokens
    endtag = 'end' + tag_name

    # Strip the quotes off the ends of the permission_type string
    permission_type = _strip_quotes(permission_type)

    nodelist_true = parser.parse(('else', endtag))
    #parser.delete_first_token()
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((endtag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    return IfPermissionNode(nodelist_true, nodelist_false, permission_type,
                            object)


@register.tag
def ifnotpermission(parser, token):
    """
    Usage:
      {% ifnotpermission [permission_type] [object] %}
        content
      {% else %}
        content
      {% endifnotpermission %}

    Calls the Permission.objects.[permission_type]() function with the current
    user and the given object.  If true, renders the contents of this tag.
    If false, renders nothing.
    """
    tokens = token.split_contents()
    tag_name, permission_type, object = tokens
    endtag = 'end' + tag_name

    # Strip the quotes off the ends of the permission_type string
    permission_type = _strip_quotes(permission_type)

    nodelist_true = parser.parse(('else', endtag))
    #parser.delete_first_token()
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse((endtag,))
        parser.delete_first_token()
    else:
        nodelist_false = template.NodeList()
    # NOTE: Since this is the NOT tag, nodelist_true and nodelist_false
    # are switched...
    return IfPermissionNode(nodelist_false, nodelist_true, permission_type,
                            object)


class IfPermissionNode(template.Node):
    def __init__(self, nodelist_true, nodelist_false, permission_type, object):
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false
        self.permission_type = permission_type
        self.object = template.Variable(object)
        self.user = template.Variable('user')

    def render(self, context):
        object = self.object.resolve(context)
        user = self.user.resolve(context)

        # Get the function Permission.objects[permission_type]() and call with
        # the current user & object
        from models.profile import Permission
        fn = getattr(Permission.objects, self.permission_type)
        has_permission = fn(user, object)

        if has_permission:
            return self.nodelist_true.render(context)
        else:
            return self.nodelist_false.render(context)
