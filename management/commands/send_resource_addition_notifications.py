from datetime import datetime
from itertools import groupby
from operator import attrgetter

from django.core.management.base import NoArgsCommand
from django.core.mail import EmailMultiAlternatives
from django.template import Context, loader
from html2text import html2text
from django.contrib.sites.models import Site

from models.notification import ResourceAdditionNotificationRequest, \
    ResourceAdditionNotification
from models.resource import ResourceNodes

from models.society import NodeSocieties
import settings
from util import group_conferences_by_series


class Command(NoArgsCommand):
    def handle_noargs(self, *args, **options):
        emails = ResourceAdditionNotificationRequest.objects. \
            only('email').distinct()
        for email in emails:
            reqs = ResourceAdditionNotificationRequest.objects. \
                filter(email=email.email)
            reqs_with_new_items = []
            for req in reqs:
                print "req: %d" % req.id
                previous_notifications = ResourceAdditionNotification.objects.\
                    filter(request=req).order_by('-date_notified')
                if previous_notifications.count():
                    last_update = previous_notifications[0].date_notified
                else:
                    last_update = req.date_created

                print "last_update: %s" % last_update

                new_societies = \
                    NodeSocieties.objects.filter(node=req.node,
                                                 date_created__gt=last_update)
                for ns in new_societies:
                    # Save record of this relationship being notified via email
                    nt = ResourceAdditionNotification()
                    nt.request = req
                    nt.resourceSocieties = ns
                    nt.date_notified = datetime.utcnow()
                    nt.save()

                new_resources = ResourceNodes.objects. \
                    filter(node=req.node, date_created__gt=last_update). \
                    order_by('resource__resource_type')
                print "new resource count: %d" % new_resources.count()
                for nr in new_resources:
                    # Save record of this relationship being notified via email
                    nt = ResourceAdditionNotification()
                    print "new notification"
                    nt.request = req
                    print "request id: %d" % req.id
                    nt.resourceNodes = nr
                    print "resourceNodes id: %d" % nr.id
                    nt.date_notified = datetime.utcnow()
                    print "date_notified: %s" % nt.date_notified
                    nt.save()
                for nr in new_resources:
                    nr.resource_type = nr.resource.resource_type.name
                print "new resource count: %d" % new_resources.count()

                if new_resources.count():
                    req.new_resources = new_resources
                    if req not in reqs_with_new_items:
                        reqs_with_new_items.append(req)

                if new_societies.count():
                    req.new_societies = new_societies
                    if req not in reqs_with_new_items:
                        reqs_with_new_items.append(req)

                print "reqs with new items count: %d" % \
                      len(reqs_with_new_items)

            if reqs_with_new_items:
                total_count = 0
                for req in reqs_with_new_items:
                    if hasattr(req, 'new_resources'):
                        total_count += req.new_resources.count()
                    if hasattr(req, 'new_societies'):
                        total_count += req.new_societies.count()
                    new_resources = [item.resource
                                     for item in req.new_resources]
                    resources_groupby = \
                        groupby(new_resources, attrgetter('resource_type'))
                    grouped_resources = {}
                    for key, values in resources_groupby:
                        values = list(values)
                        if key.name == 'conference':
                            reordered_conferences = []
                            grouped_conferences = \
                                group_conferences_by_series(values)
                            for conference in grouped_conferences:
                                reordered_conferences.append(conference)
                                if hasattr(conference, 'other_conferences'):
                                    for item in conference.other_conferences:
                                        reordered_conferences.append(item)
                            values = reordered_conferences
                        grouped_resources[key] = values
                    req.grouped_resources = grouped_resources
                subject = \
                    "%d New Topic Alert%s from IEEE Technology Navigator" % \
                    (total_count,  # count of both resources and societies
                     "s" if total_count > 1 else "")
                context = Context({
                    "notification_requests": reqs_with_new_items,
                    "domain": Site.objects.get_current()
                })
                template = loader.get_template('email/notify_email.html')
                body_html = template.render(context)
                body_text = html2text(body_html)
                msg = EmailMultiAlternatives(subject, body_text,
                                             settings.DEFAULT_FROM_EMAIL,
                                             [email.email])
                msg.attach_alternative(body_html, 'text/html')
                msg.send()
