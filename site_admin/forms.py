from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import *

from ieeetags.models import Filter, Node, NodeType, Society, Resource, ResourceType, Profile
from ieeetags.fields import MultiSearchField
from ieeetags.widgets import MultiSearchWidget, DisplayOnlyWidget, CheckboxSelectMultipleColumns

def _make_choices(list1):
    for item in list1:
        yield item, item

class ModifiedFormBase(Form):
    """
    Adds support for outputting one field/table row at a time.
    """
    def as_table(self, field_name=None):
        "Just like Form.as_table(), except can render a single field (row) at a time."
        if field_name is None:
            return self._html_output(u'<tr><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>', u'<tr><td colspan="2">%s</td></tr>', '</td></tr>', u'<br />%s', False)
        else:
            # Only render a single field as a table row
            self.backup_fields = self.fields
            self.fields = {
                field_name: self.backup_fields[field_name]
            }
            result = self._html_output(u'<tr><th>%(label)s</th><td>%(errors)s%(field)s%(help_text)s</td></tr>', u'<tr><td colspan="2">%s</td></tr>', '</td></tr>', u'<br />%s', False)
            self.fields = self.backup_fields
            return result

def autostrip(cls):
    "Convert a form so that each CharField's value is automatically stripped."
    fields = [(key, value) for key, value in cls.base_fields.iteritems() if isinstance(value, CharField)]
    for field_name, field_object in fields:
        def get_clean_func(original_clean):
            return lambda value: original_clean(value and value.strip())
        clean_func = get_clean_func(getattr(field_object, 'clean'))
        setattr(field_object, 'clean', clean_func)
    return cls
# ------------------------------------------------------------------------------

class CreateTagForm(Form):
    name = CharField(max_length=100, label='Tag Name')
    sectors = ModelMultipleChoiceField(queryset=Node.objects.getSectors(), label='Sector', widget=SelectMultiple(attrs={'size':3}))
    filters = ModelMultipleChoiceField(queryset=Filter.objects.all(), widget=CheckboxSelectMultipleColumns(columns=2), required=False, label='Filters')
    related_tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', label='Related Tags', widget_label='Associate Related Tags', widget=MultiSearchWidget(remove_link_flyover_text='Remove Tag from Tag'))

CreateTagForm = autostrip(CreateTagForm)

class EditTagForm(Form):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=100, label='Tag Name')
    parents = ModelMultipleChoiceField(queryset=Node.objects.getSectors(), label='Sectors', widget=CheckboxSelectMultiple())
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies', label='Societies')
    filters = ModelMultipleChoiceField(queryset=Filter.objects.all(), widget=CheckboxSelectMultipleColumns(columns=2), required=False, label='Filters')
    #num_resources = models.IntegerField(required=False, label='Resources')
    related_tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', label='Related Tags', widget_label='Associate Related Tags with this Tag' ,widget=MultiSearchWidget(remove_link_flyover_text='Remove Tag from Tag'))

EditTagForm = autostrip(EditTagForm)

class LoginForm(Form):
    username = CharField(max_length=30, label='User Name:')
    password = CharField(widget=PasswordInput(), max_length=1000, label='Password:')

LoginForm = autostrip(LoginForm)

class ForgotPasswordForm(Form):
    username = CharField(max_length=30, label='Please enter your username:', required=False)
    email = CharField(label='Or the email associated with the account:', required=False)

ForgotPasswordForm = autostrip(ForgotPasswordForm)

class ChangePasswordForm(Form):
    password1 = CharField(widget=PasswordInput(), label='Please enter your new password:')
    password2 = CharField(widget=PasswordInput(), label='Type your password again:')

class CreateResourceForm(Form):
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all())
    ieee_id = IntegerField(required=False)
    name = CharField(max_length=500)
    description = CharField(widget=Textarea, max_length=1000, required=False)
    url = CharField(max_length=1000, required=False)
    nodes = MultiSearchField(label='Tags', model=Node, search_url='/admin/ajax/search_tags')
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies')
    priority_to_tag = BooleanField(required=False)

CreateResourceForm = autostrip(CreateResourceForm)

class EditResourceForm(Form):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=500, label='Resource Name')
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all(), widget=DisplayOnlyWidget(field_type=type(ModelChoiceField), use_capwords=True), label='Resource Type')
    ieee_id = CharField(required=False, label='ID')
    description = CharField(widget=Textarea, max_length=1000, required=False)
    url = CharField(max_length=1000, required=False, label='URL')
    nodes = MultiSearchField(label='Tags', model=Node, search_url='/admin/ajax/search_tags', widget_label='Associate Tags with this Resource', show_create_tag_link=True, widget=MultiSearchWidget(remove_link_flyover_text='Remove Tag from Resource'))
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies', label='Societies')
    priority_to_tag = BooleanField(required=False)
    standard_status = ChoiceField(choices=_make_choices(Resource.STANDARD_STATUSES), required=False)
    keywords = CharField(max_length=1000, required=False)

EditResourceForm = autostrip(EditResourceForm)

class SocietyForm(ModifiedFormBase):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=500)
    abbreviation = CharField(max_length=20)
    url = CharField(max_length=1000, required=False)
    users = ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags')
    resources = MultiSearchField(model=Resource, search_url='/admin/ajax/search_resources')

SocietyForm = autostrip(SocietyForm)

class SearchTagsForm(Form):
    tag_name = CharField(max_length=100)

class SearchSocietiesForm(Form):
    society_name = CharField(max_length=100)

class SearchResourcesForm(Form):
    resource_name = CharField(max_length=100)

class UserForm(Form):
    id = IntegerField(widget=HiddenInput(), required=False)
    username = CharField(max_length=30)
    first_name = CharField(max_length=500, required=False)
    last_name = CharField(max_length=500, required=False)
    email = CharField(max_length=1000)
    is_staff = BooleanField(required=False)
    is_superuser = BooleanField(required=False)
    role = ChoiceField(choices=Profile.ROLES)
    societies = ModelMultipleChoiceField(queryset=Society.objects.all(), required=False)

UserForm = autostrip(UserForm)

class ManageSocietyForm(Form):
    # No longer used, page is live-edit (resources are just links)
    #resources = MultiSearchField(model=Resource, search_url='/admin/ajax/search_resources')
    tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', widget_label='Associate Tags with this Society', show_create_tag_link=True, widget=MultiSearchWidget(attrs={'classMetadata':'showSelectedOptions:false' }))

class MissingResourceForm(Form):
    society = ModelChoiceField(queryset=Society.objects.all(), widget=HiddenInput())
    name = CharField(max_length=1000, widget=DisplayOnlyWidget(field_type=CharField))
    email = CharField(max_length=1000, widget=DisplayOnlyWidget(field_type=CharField))
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all())
    description = CharField(label='Description of the missing resource', widget=Textarea, max_length=5000)

MissingResourceForm = autostrip(MissingResourceForm)
