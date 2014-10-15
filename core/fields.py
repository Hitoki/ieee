from django.forms import fields
import json
import widgets


class MultiSearchField(fields.Field):
    """
    Custom form widget.  Allows user to type a search phrase into the INPUT,
    and shows results in an AJAX dropdown.  Users can select multiple values.

    Uses extensive Javascript.
    """
    widget = widgets.MultiSearchWidget

    def __init__(self, model, search_url, format='simple', widget_label=None,
                 show_create_tag_link=False, society_id=None, *args, **kwargs):
        super(MultiSearchField, self).__init__(*args, **kwargs)
        self.required = False
        self.model = model
        self.search_url = search_url
        self.widget.set_model(model)
        self.widget.set_search_url(search_url)
        self.widget.set_format(format)
        self.widget.set_widget_label(widget_label)
        self.widget.set_show_create_tag_link(show_create_tag_link)
        self.widget.set_society_id(society_id)

    def clean(self, value):
        """
        Returns an array of models.
        """
        super(MultiSearchField, self).clean(value)
        if value is None:
            return None

        #print 'MultiSearchField.clean()'
        #print '  value:', value
        #print '  type(value):', type(value)

        data = json.loads(value)
        objects = []
        for item in data:
            objects.append(self.model.objects.get(id=int(item['value'])))
        return objects
