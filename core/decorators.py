from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import REDIRECT_FIELD_NAME


def optional_login_required(function=None,
                            redirect_field_name=REDIRECT_FIELD_NAME):
    """
    Decorator that performs simple app setting check before invoking or
    bypassing standard Django login_required decorator.
    """
    if settings.REQUIRE_LOGIN_FOR_NON_ADMIN_VIEWS:
        return login_required(function, redirect_field_name)
    else:
        return function
