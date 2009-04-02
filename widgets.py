from django.db.models import Model
from django.core.urlresolvers import reverse
from django.forms import widgets
from django.utils.safestring import mark_safe
from django.utils import simplejson as json
from django.utils.html import escape
from urllib import quote

class MultiSearchWidget(widgets.Widget):
    "Renders a widget that allows users to search for and select multiple options.  Uses AJAX to load search options."
    search_url = None
    model = None
    
    def __init__(self, attrs=None):
        super(MultiSearchWidget, self).__init__(attrs)
        
    def set_search_url(self, search_url):
        self.search_url = search_url

    def set_format(self, format):
        if format != 'simple' and format != 'full_tags_table':
            raise Exception('Unknown format "%s"' % format)
        self.format = format

    def set_widget_label(self, widget_label):
        self.widget_label = widget_label

    def set_model(self, model):
        self.model = model

    def render(self, name, value, attrs=None):
        #print 'MultiSearchWidget()'
        #print '  name:', name
        #print '  value:', value
        #print '  type(value):', type(value)
        
        if type(value) is str or type(value) is unicode:
            # Got a JSON string, convert
            data = json.loads(value)
            objects = []
            for item in data:
                objects.append(self.model.objects.get(id=int(item['value'])))
        else:
            # Got an array of objects
            objects = value
        
        results = []
        if objects is not None:
            for object in objects:
                if self.format == 'simple':
                    results.append({
                        'name': str(object),
                        'value': str(object.id),
                    })
                elif self.format == 'full_tags_table':
                    results.append({
                        'name': object.name_with_sector(),
                        'name_link': reverse('admin_edit_tag', args=[object.id]) + '?return_url=%s' % quote('/admin/?hash=' + quote('#tab-tags-tab')),
                        'value': object.id,
                        'tag_name': object.name,
                        'sector_names': object.parent_names(),
                        'num_societies': len(object.societies.all()),
                        'num_related_tags': len(object.related_tags.all()),
                        'num_filters': len(object.filters.all()),
                        'num_resources': len(object.resources.all()),
                    })
        
        initial_data = json.dumps(results)
        
        if self.widget_label is None:
            widget_label = 'Associate %s' % name
        else:
            widget_label = self.widget_label
        
        output = []
        output.append('<div id="%s" class="multi-search {searchUrl:\'%s\', format:\'%s\'}">' % ('multisearch_'+name, self.search_url, self.format))
        output.append('    <input type="hidden" name="%s" value="%s" class="multi-search-data" />' % (name, escape(initial_data)))
        output.append('    %s: <input class="multi-search-input blur-text {text:\'(Type a few characters to bring up matching %s)\', blurClass:\'multi-search-input-blur\' }" />' % (widget_label, name))
        output.append('    <div class="multi-search-selected-options">')
        output.append('    </div>')
        output.append('</div>')
        
        return mark_safe(u'\n'.join(output))

def make_display_only(field, **kwargs):
    if kwargs is None:
        kwargs = {}
    kwargs.update({
        'field_type': type(field),
    })
    field.widget = DisplayOnlyWidget(**kwargs)

class DisplayOnlyWidget(widgets.HiddenInput):
    "Renders a widget as a text label with a hidden input.  Allows a field to be display but not edited."
    is_hidden = False
    
    # TODO: get rid of is_multi_search, use the field_type instead
    
    def __init__(self, field_type, model=None, is_multi_search=False, use_capwords=False, attrs=None):
        "If a model is given, the display will be the str() of the instance, and value will be treated as the ID of the instance."
        #print 'DisplayOnlyWidget.__init__()'
        super(DisplayOnlyWidget, self).__init__(attrs)
        self.field_type = field_type
        self.model = model
        self.is_multi_search = is_multi_search
        self.use_capwords = use_capwords
        #print '  self.is_multi_search:', self.is_multi_search
        
    def render(self, name, value, attrs=None):
        import string
        from django.utils.html import escape
        from django.db.models.query import QuerySet
        
        #print 'DisplayOnlyWidget.render()'
        #print '  name:', name
        #print '  value:', value
        #print '  type(value):', type(value)
        #print '  self.is_multi_search:', self.is_multi_search
        #print '  self.field_type:', self.field_type

        if self.is_multi_search:
            if type(value) is QuerySet:
                # Got queryset, create a list of the names
                if self.is_multi_search:
                    print 'Making JSON list'
                    # Make a JSON list
                    result = ''
                    display = []
                    data = []
                    for object in value.all():
                        data.append({
                            'name': str(object),
                            'value': object.id,
                        })
                        display.append(str(object))
                    super_render = super(DisplayOnlyWidget, self).render(name, json.dumps(data), attrs)
                    display = string.join(display, ', ')
            
            elif type(value) is string or type(value) is unicode:
                # Got JSON data
                data = json.loads(value)
                display = []
                super_render = super(DisplayOnlyWidget, self).render(name, value, attrs)
                for item in data:
                    display.append(item['name'])
                display = string.join(display, ', ')
                
        else:
        
            display = value
            if value is not None and self.model is not None:
                # Lookup model by id, treat value as the id (or list of id's)
                
                if type(value) is list:
                    # Convert the list of id's into a list of labels
                    results = []
                    for id in value:
                        results.append(str(self.model.objects.get(id=int(id))))
                    display = string.join(results, ', ')
                
                elif type(value) is QuerySet:
                    pass
                    
                else:
                    # Convert the id into a label
                    display = str(self.model.objects.get(id=int(value)))
            
            if value is None:
                value = ''
                super_render = ''
                display = ''
            
            elif type(value) is QuerySet:
                # Must be a select or array of checkboxes
                display_results = []
                super_render = ''
                for item in value.all():
                    super_render += super(DisplayOnlyWidget, self).render(name, item.id, attrs)
                    display_results.append(str(item))
                display = string.join(display_results, ', ')
                
            elif type(value) is list:
                # Convert a list of id's into multiple hidden inputs
                super_render = ''
                for item in value:
                    super_render += super(DisplayOnlyWidget, self).render(name, item, attrs)
                
            elif isinstance(value, Model):
                super_render = super(DisplayOnlyWidget, self).render(name, value.id, attrs)
                display = str(value)
                if self.use_capwords:
                    display = string.capwords(display)
            
            else:
                # Render as a simple hidden input
                super_render = super(DisplayOnlyWidget, self).render(name, value, attrs)
        
        return mark_safe(u'%s\n%s' % (super_render, escape(display)))
