from django import template

register = template.Library()


@register.tag(name='eval')
def eval_(parser, token):
    """
    Allows evaluating code in templates, for more flexibility.
    """
    tag_name, expression = token.split_contents()
    return EvalNode(expression)


class EvalNode(template.Node):
    def __init__(self, expression):
        self.expression = expression

    def render(self, context):
        #print 'calling eval(%s)' % repr(self.expression)
        result = eval(self.expression, {}, context)
        #print 'done'
        return result
