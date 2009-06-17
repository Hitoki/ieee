
from django.forms import *

#class ImportForm(Form):
#    text = CharField(widget=Textarea)

class FeedbackForm(Form):
    name = CharField(max_length=1000)
    email = EmailField(max_length=1000)
    comments = CharField(widget=Textarea, max_length=5000)

class DebugSendEmailForm(Form):
    email = EmailField(max_length=1000)
    