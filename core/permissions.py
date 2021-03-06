"""
DEPRECATED: Should use the Permissions model instead of this module.
"""

import logging
from webapp.models.profile import Profile


#def require_staff(request):
#    #logging.debug('request.user.is_staff: %d' % request.user.is_staff)
#    if not request.user.is_staff and not request.user.is_superuser:
#        raise Exception('You must be logged in as a staff member to access '
#                        'this page.')

# TODO: This is deprecated, use @admin_required instead.
#def require_superuser(request):
#    #logging.debug('request.user.is_superuser: %d' %
#                   request.user.is_superuser)
#    if not request.user.is_superuser:
#        raise Exception('You must be logged in as a super user to access '
#                        'this page.')


def require_society_user(request, society_id):
    """
    DEPRECATED: Make sure the user is associated with the society.
    """
    #print 'request.user.is_superuser:', request.user.is_superuser
    if request.user.profile.role != Profile.ROLE_ADMIN \
            and request.user.profile.role != Profile.ROLE_SOCIETY_ADMIN \
            and request.user.societies.filter(id=society_id).count() == 0:
        raise Exception('Your account does not have permissions to access '
                        'this society page.')
