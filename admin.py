'Adds models to the django admin page.'

from django.contrib import admin
import django.db.models
import models
import inspect

objects = inspect.getmembers(models)
for name, value in objects:
    # import ipdb; ipdb.set_trace()
    if inspect.isclass(value) and issubclass(value, django.db.models.Model) and value.__module__ == 'ieeetags.models' and not value._meta.abstract:
        admin.site.register(value)
