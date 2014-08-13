from django import forms
from django.core.exceptions import ObjectDoesNotExist
from django.utils.safestring import mark_safe
from models.node import Node
from models.conference_application import ConferenceApplication, TagKeyword
from models.favorites import UserFavorites

class FeedbackForm(forms.Form):
    name = forms.CharField(max_length=1000)
    email = forms.EmailField(max_length=1000)
    comments = forms.CharField(widget=forms.Textarea, max_length=5000)


#class ImportForm(Form):
#    text = CharField(widget=Textarea)


class DebugSendEmailForm(forms.Form):
    email = forms.EmailField(max_length=1000)


class ConferenceApplicationForm(forms.ModelForm):
    keywords_in = forms.CharField(label=mark_safe('Keywords:<span class="required">*</span>'), required=False)
    keywords_out = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = ConferenceApplication
        fields = ['name', ]

    def save(self, commit=True):
        super(ConferenceApplicationForm, self).save(commit)
        keywords_out = self.cleaned_data['keywords_out']
        keywords = keywords_out.split('|')
        for keyword_name in keywords:
            try:
                node = Node.objects.get(name=keyword_name)
            except ObjectDoesNotExist:
                node = None
            keyword, created = \
                TagKeyword.objects.get_or_create(name=keyword_name, tag=node)
            self.instance.keywords.add(keyword)

class UserFavoriteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(UserFavoriteForm, self).__init__(*args, **kwargs)
        self.fields['user'].required=False
        self.fields['user'].widget = forms.HiddenInput();

    class Meta:
        model = UserFavorites