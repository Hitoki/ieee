from django import template

register = template.Library()

@register.tag(name='eval')
def eval_(parser, token):
    #print 'eval()'
    #print '  parser:', parser
    #print '  token:', token
    
    #print '  token.split_contents():', token.split_contents()
    
    tag_name, expression = token.split_contents()
    #print '  tag_name:', tag_name
    #print '  expression:', expression
    
    return EvalNode(expression)
    
class EvalNode(template.Node):
    def __init__(self, expression):
        self.expression = expression
    
    def render(self, context):
        
        #print 'calling eval(%s)' % repr(self.expression)
        result = eval(self.expression, {}, context)
        #print 'done'
        
        return result
