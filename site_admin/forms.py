from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.forms import *

from ieeetags.models import Society, Resource, Profile

from ieeetags.fields import MultiSearchField
from ieeetags.widgets import MultiSearchWidget, DisplayOnlyWidget, CheckboxSelectMultipleColumns
from ieeetags import url_checker
from new_models.node import Node
from new_models.types import NodeType, ResourceType, Filter
from new_models.utils import list_to_choices


TRISTATE_CHOICES = [
    'no change',
    'yes',
    'no',
]

TRISTATE_CHOICES_RESOURCES = [
    ('no change', 'No change'),
    ('yes', 'Yes for all resources'),
    ('no', 'No for all resources'),
]

TRISTATE_CHOICES_TAGS = [
    ('no change', 'No change'),
    ('yes', 'Apply to all topics'),
    ('no', 'Remove from all topics'),
]

def _make_choices(list1, add_blank=False, nice_format=True):
    if add_blank:
        yield '', '(none)'
    for item in list1:
        if nice_format:
            value = str(item).capitalize()
        yield item, value

def _make_choices_with_blank(list1):
    return _make_choices(list1, True)

class ModifiedFormBase(Form):
    "Adds support for outputting one field/table row at a time."
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
    name = CharField(max_length=100, label='Name', show_hidden_initial=True)
    sectors = ModelMultipleChoiceField(queryset=Node.objects.getSectors(), label='Sectors', widget=CheckboxSelectMultipleColumns(columns=3), required=False)
    definition = CharField(widget=Textarea(), label='Definitiion', required=False)
    filters = ModelMultipleChoiceField(queryset=Filter.objects.all(), widget=CheckboxSelectMultipleColumns(columns=2), required=False, label='Filters')
    related_tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', label='Related Topics', widget_label='Associate Related Topics', show_create_tag_link=True, widget=MultiSearchWidget(remove_link_flyover_text='Remove Topic from Topic', blur_text='Type a few characters to bring up matching topics'))
        
    def __init__(self, user, *args, **kwargs):
        super(CreateTagForm, self).__init__(*args, **kwargs)
        self.fields['societies'] = ModelMultipleChoiceField(queryset=Society.objects.getForUser(user), label='Organization', widget=CheckboxSelectMultipleColumns(columns=3))

    def clean_name(self):
        data = self.cleaned_data['name']
        
        # Admins can create duplicate tags. Other roles cannot.
        if self.user_role in [Profile.ROLE_ADMIN]:
            # If the name has changed check to see if it already exists in the DB.
            # If the name value has not changed the user is resubmitting the same name, despite the warning that it is a duplicate.
            if 'name' in self._get_changed_data() and len(Node.objects.getTagsByName(data)):
                raise forms.ValidationError("A topic with this name already exists. To create this tag anyway resubmit the form.")
        else:
            if len(Node.objects.getTagsByName(data)):
                raise forms.ValidationError("A topic named \"%s\" already exists. As a %s you do not have permission to create a duplicate tag. Only Administrators can do so." % (data, self.user_role.replace('_', ' ').title()))
        return data
                

CreateTagForm = autostrip(CreateTagForm)

class EditTagForm(Form):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=100, label='Name')
    parents = ModelMultipleChoiceField(queryset=Node.objects.getSectors(), label='Sectors', widget=CheckboxSelectMultipleColumns(columns=3), required=False)
    definition = CharField(widget=Textarea(), required=False)
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies', label='Organization', widget_label='Associate organizations',widget=MultiSearchWidget(remove_link_flyover_text='Remove Organization from Topic',blur_text='Type a few characters to bring up matching organizations'))
    filters = ModelMultipleChoiceField(queryset=Filter.objects.all(), widget=CheckboxSelectMultipleColumns(columns=2), required=False, label='Filters')
    related_tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', label='Related Topics', widget_label='Associate Related Topics with this Topic',show_create_tag_link=True, widget=MultiSearchWidget(remove_link_flyover_text='Remove Tag from Tag', blur_text='Type a few characters to bring up matching topics'))

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

class CreateFakeTagsForm(Form):
	total_num_tags = IntegerField()

class CreateResourceForm(Form):
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all())
    ieee_id = CharField(required=False, label='ID')
    name = CharField(max_length=500)
    description = CharField(widget=Textarea, max_length=1000, required=False)
    url = CharField(max_length=1000, required=False)
    nodes = MultiSearchField(label='Tags', model=Node, search_url='/admin/ajax/search_tags')
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies')
    priority_to_tag = BooleanField(required=False)
    completed = BooleanField(required=False)
    standard_status = ChoiceField(choices=_make_choices_with_blank(Resource.STANDARD_STATUSES), required=False)
    keywords = CharField(max_length=1000, required=False)
    conference_series = CharField(max_length=100, required=False)
    year = IntegerField(required=False)
    date = DateField(required=False)

CreateResourceForm = autostrip(CreateResourceForm)

class EditResourceForm(Form):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=500, label='Resource Name')
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all(), widget=DisplayOnlyWidget(field_type=type(ModelChoiceField), use_capwords=True), label='Resource Type')
    conference_series = CharField(required=False)
    ieee_id = CharField(required=False, label='ID')
    description = CharField(widget=Textarea, max_length=1000, required=False)
    url = CharField(max_length=1000, required=False, label='URL')
    nodes = MultiSearchField(label='Tags', model=Node, search_url='/admin/ajax/search_tags', widget_label='Associate Topics with this Resource', show_create_tag_link=True, widget=MultiSearchWidget(remove_link_flyover_text='Remove Topic from Resource', blur_text='Type a few characters to bring up matching topics'))
    societies = MultiSearchField(model=Society, search_url='/admin/ajax/search_societies', label='Organization', widget=MultiSearchWidget(remove_link_flyover_text='Remove Organization from Resource'))
    priority_to_tag = BooleanField(required=False)
    completed = BooleanField(required=False)
    standard_status = ChoiceField(choices=_make_choices(Resource.STANDARD_STATUSES), required=False)
    keywords = CharField(max_length=1000, required=False)
    year = IntegerField(required=False)
    date = DateField(required=False)

EditResourceForm = autostrip(EditResourceForm)

class SocietyForm(ModifiedFormBase):
    id = IntegerField(widget=HiddenInput(), required=False)
    name = CharField(max_length=500)
    abbreviation = CharField(max_length=20)
    description = CharField(widget=Textarea, max_length=5000, required=False)
    url = CharField(max_length=1000, required=False)
    users = ModelMultipleChoiceField(queryset=User.objects.all(), required=False)
    tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags')
    resources = MultiSearchField(model=Resource, search_url='/admin/ajax/search_resources')
    
    def clean_url(self):
        data = self.cleaned_data['url']
        
        (url_status, url_error) = url_checker.check_url(data, 4)
        
        if url_error != '':
            raise forms.ValidationError(url_error)
        return data

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
    password1 = CharField(label='Enter a password:', max_length=100, widget=PasswordInput(), required=False)
    password2 = CharField(label='Enter the password again:', max_length=100, widget=PasswordInput(), required=False)
    role = ChoiceField(choices=list_to_choices(Profile.ROLES))
    societies = ModelMultipleChoiceField(queryset=Society.objects.all(), required=False)

UserForm = autostrip(UserForm)

class ManageSocietyForm(Form):
    # No longer used, page is live-edit (resources are just links)
    #resources = MultiSearchField(model=Resource, search_url='/admin/ajax/search_resources')
    tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', widget_label='Associate Topics with this Organization', show_create_tag_link=True, widget=MultiSearchWidget(attrs={'classMetadata':'showSelectedOptions:false' }))

class MissingResourceForm(Form):
    society = ModelChoiceField(queryset=Society.objects.all(), widget=HiddenInput())
    name = CharField(max_length=1000, widget=DisplayOnlyWidget(field_type=CharField))
    email = CharField(max_length=1000, widget=DisplayOnlyWidget(field_type=CharField))
    resource_type = ModelChoiceField(queryset=ResourceType.objects.all())
    description = CharField(label='Description of the missing resource', widget=Textarea, max_length=5000)

MissingResourceForm = autostrip(MissingResourceForm)

class ImportFileForm(Form):
    file = FileField()

class EditResourcesForm(Form):
    assign_tags = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', label='Assign Topics', widget_label='Assign Topics', show_create_tag_link=True, widget=MultiSearchWidget(remove_link_flyover_text='Remove Tag', blur_text='Type a few characters to bring up matching topics'))
    priority = ChoiceField(choices=TRISTATE_CHOICES_RESOURCES, widget=RadioSelect())
    completed = ChoiceField(choices=TRISTATE_CHOICES_RESOURCES, widget=RadioSelect())

class EditTagsForm(Form):
    emerging_technologies_filter = ChoiceField(choices=TRISTATE_CHOICES_TAGS, widget=RadioSelect(), label='Emerging Technologies')
    foundation_technologies_filter = ChoiceField(choices=TRISTATE_CHOICES_TAGS, widget=RadioSelect(), label='Foundation Technologies')
    hot_topics_filter = ChoiceField(choices=TRISTATE_CHOICES_TAGS, widget=RadioSelect(), label='Hot Topics')
    market_areas_filter = ChoiceField(choices=TRISTATE_CHOICES_TAGS, widget=RadioSelect(), label='Market Areas')

class EditClusterForm2(ModelForm):
    topics = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', widget=MultiSearchWidget(remove_link_flyover_text='Remove Topic from this Topic Area', blur_text='Type a few characters to bring up matching topics'), help_text="As you associate Topics with the Topic Area, based upon your choices, the system will automatically associate the Topic Area with relevant IEEE Organizations. The system does so by searching for any Organizations that are already associated with the Topic. The Topic Area is then automatically associated with any Organization already associated with one or more of the Topic Area's Topics.")
    societies = ModelMultipleChoiceField(queryset=Society.objects.all(), label='Organization', widget=CheckboxSelectMultipleColumns(columns=3), required=False)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        
        super(EditClusterForm2, self).__init__(*args, **kwargs)
        if self.instance.id ==  None:
            self.fields.pop('societies')


    class Meta:
        model = Node
        fields = ['id','name']


class EditClusterForm(ModelForm):
    topics = MultiSearchField(model=Node, search_url='/admin/ajax/search_tags', widget=MultiSearchWidget(remove_link_flyover_text='Remove Topic from this Topic Area', blur_text='Type a few characters to bring up matching topics'))
    societies = ModelMultipleChoiceField(queryset=Society.objects.all(), label='Organization', widget=CheckboxSelectMultipleColumns(columns=3))

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        society = kwargs.pop('society', None)
        super(EditClusterForm, self).__init__(*args, **kwargs)
        
        user_role = user.get_profile().role
        if user_role  == Profile.ROLE_SOCIETY_MANAGER:
            # Name is read-only
            self.fields['name'] = CharField(widget=DisplayOnlyWidget(field_type=CharField))

            # Organizations are hidden
            self.fields['societies'].widget =  self.fields['societies'].hidden_widget()

            # Show all topics associated with this topic area
            allnodes = self.instance.child_nodes.all()            

            # Topics are a checkbox list
            self.fields['topics'] = ModelMultipleChoiceField(queryset=allnodes, widget=CheckboxSelectMultipleColumns(columns=3), required=False)

            # Topics already associated with this society are prechecked.
            initialnodes = allnodes.filter(societies__id=society.id);
            self.fields['topics'].initial = initialnodes
        elif user_role == Profile.ROLE_ADMIN and society != None:
            # Organizations are hidden
            self.fields['societies'].widget =  self.fields['societies'].hidden_widget()

            # Show all topics associated with this topic area
            allnodes = self.instance.child_nodes.all()            

            # Topics are a checkbox list
            self.fields['topics'] = ModelMultipleChoiceField(queryset=allnodes, widget=CheckboxSelectMultipleColumns(columns=3), required=False)

            # Topics already associated with this society are prechecked.
            initialnodes = allnodes.filter(societies__id=society.id);
            self.fields['topics'].initial = initialnodes

                

    class Meta:
        model = Node
        fields = ['id','name','societies']

class ItemsPerPageForm(Form):
    _ITEMS_PER_PAGE = [
        (20, 20),
        (50, 50),
        (100, 100),
        (1000000, 'all'),
    ]
    items_per_page = ChoiceField(choices=_ITEMS_PER_PAGE, widget=Select(attrs={ 'class': 'items-per-page'}))

class SendEmailAllUsersForm(Form):
    subject = CharField()
    body = CharField(widget=Textarea())
    send_email = BooleanField(widget=HiddenInput(), required=False)

class AssignProfilingCategoryForm(Form):
    category = CharField(required=False)
