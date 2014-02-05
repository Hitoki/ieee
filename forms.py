from django import forms
from django.core.exceptions import ObjectDoesNotExist
from models.node import Node
from models.conference_application import ConferenceApplication, TagKeyword


class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=1000)
    email = forms.EmailField(max_length=1000)
    comments = forms.CharField(widget=forms.Textarea, max_length=5000)


#class ImportForm(Form):
#    text = CharField(widget=Textarea)


class DebugSendEmailForm(forms.Form):
    email = forms.EmailField(max_length=1000)


class ConferenceApplicationForm(forms.ModelForm):
    keywords_text = forms.CharField(label="Keywords", required=False)

    class Meta:
        model = ConferenceApplication
        fields = ['name', ]

    def save(self, commit=True):
        super(ConferenceApplicationForm, self).save(commit)
        keywords_text = self.cleaned_data['keywords_text']
        print 'keywords_text:', keywords_text
        keywords = keywords_text.split(', ')
        for keyword_name in keywords:
            try:
                node = Node.objects.get(name=keyword_name)
            except ObjectDoesNotExist:
                node = None
            keyword, created = \
                TagKeyword.objects.get_or_create(name=keyword_name, tag=node)
            self.instance.keywords.add(keyword)
