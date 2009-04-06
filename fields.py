
from django.forms import fields
from django.utils import simplejson as json
import widgets

class MultiSearchField(fields.Field):
    widget = widgets.MultiSearchWidget
    
    def __init__(self, model, search_url, format='simple', widget_label=None, show_create_tag_link=False, *args, **kwargs):
        super(MultiSearchField, self).__init__(*args, **kwargs)
        self.required = False
        self.model = model
        self.search_url = search_url
        self.widget.set_model(model)
        self.widget.set_search_url(search_url)
        self.widget.set_format(format)
        self.widget.set_widget_label(widget_label)
        self.widget.set_show_create_tag_link(show_create_tag_link)

    def clean(self, value):
        "Returns an array of models."
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
