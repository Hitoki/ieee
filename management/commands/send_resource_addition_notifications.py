from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from ieeetags.models import Node, ResourceNodes, ResourceAdditionNotificationRequest, ResourceAdditionNotification, NodeSocieties
from django.core.mail import send_mail, EmailMultiAlternatives
from datetime import datetime
from django.template import Context, RequestContext, loader
from html2text import html2text
import settings
from django.contrib.sites.models import Site

class Command(NoArgsCommand):

    def handle_noargs(self, *args, **options):

        emails = ResourceAdditionNotificationRequest.objects.only('email').distinct()
        for email in emails:
            reqs = ResourceAdditionNotificationRequest.objects.filter(email=email.email)
            reqs_with_new_items = []
            for req in reqs:
                previous_notifications = ResourceAdditionNotification.objects.filter(request=req).order_by('-date_notified')
                if previous_notifications.count():
                    last_update = previous_notifications[0].date_notified
                else:
                    last_update = req.date_created

                new_societies = NodeSocieties.objects.filter(node=req.node, date_created__gt=last_update)
                for ns in new_societies:
                    # Save record of this relationship being notified via email
                    nt = ResourceAdditionNotification()
                    nt.request = req
                    nt.resourceSocieties = ns
                    nt.date_notified = datetime.utcnow()
                    nt.save()
                
                new_resources = ResourceNodes.objects.filter(node=req.node, date_created__gt=last_update).order_by('resource__resource_type')
                for nr in new_resources:
                    # Save record of this relationship being notified via email
                    nt = ResourceAdditionNotification()
                    nt.request = req
                    nt.resourceNodes = nr
                    nt.date_notified = datetime.utcnow()
                    nt.save()

                if new_resources.count():
                    req.new_resources = new_resources
                    if req not in reqs_with_new_items:
                        reqs_with_new_items.append(req)

                if new_societies.count():
                    req.new_societies = new_societies
                    if req not in reqs_with_new_items:
                        reqs_with_new_items.append(req)

            if len(reqs_with_new_items):
                context = Context({
                    "notification_requests": reqs_with_new_items,
                    "domain": Site.objects.get_current()
                })
                body = loader.get_template('email/notify_email.html').render(context)
        
                htmlbody = body
                body = html2text(body)
                msg = EmailMultiAlternatives("New resource alert", body , settings.DEFAULT_FROM_EMAIL, [email.email])
                msg.attach_alternative(htmlbody, 'text/html')
                msg.send()


