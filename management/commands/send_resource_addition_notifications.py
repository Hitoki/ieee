from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from ieeetags.models import Node, ResourceNodes, ResourceNodeNotificationRequest, ResourceNodeNotification
from django.core.mail import send_mail, EmailMultiAlternatives
from datetime import datetime
from django.template import Context, RequestContext, loader
from html2text import html2text
import settings

class Command(NoArgsCommand):

    def handle_noargs(self, *args, **options):

        emails = ResourceNodeNotificationRequest.objects.all().distinct('email')
        for email in emails:
            reqs = ResourceNodeNotificationRequest.objects.filter(email=email.email)
            reqs_with_new_resources = []
            for req in reqs:
                previous_notifications = ResourceNodeNotification.objects.filter(request=req).order_by('-date_notified')
                if previous_notifications.count():
                    last_update = previous_notifications[0].date_notified
                else:
                    last_update = req.date_created
                
                new_resources = ResourceNodes.objects.filter(node=req.node, date_created__gt=last_update)
                for nr in new_resources:
                    # Save record of this relationship being notified via email
                    nt = ResourceNodeNotification()
                    nt.request = req
                    nt.resourceNodes = nr
                    nt.date_notified = datetime.utcnow()
                    nt.save()


                if new_resources.count():
                    req.new_resources = new_resources
                    reqs_with_new_resources.append(req)

            context = Context({
                "notification_requests": reqs_with_new_resources
            })
            body = loader.get_template('email/notify_email.html').render(context)
    
            htmlbody = body
            body = html2text(body)
            msg = EmailMultiAlternatives("IEEE Technav new resource notification", body , settings.DEFAULT_FROM_EMAIL, [email.email])
            msg.attach_alternative(htmlbody, 'text/html')
            msg.send()


