from django.core.management.base import NoArgsCommand, BaseCommand, CommandError
from ieeetags.models import Node, ResourceNodes, ResourceNodeNotificationRequest, ResourceNodeNotification
from django.core.mail import send_mail
from datetime import datetime
import settings

class Command(NoArgsCommand):

    def handle_noargs(self, *args, **options):

        emails = ResourceNodeNotificationRequest.objects.all().distinct('email')
        for email in emails:
            email_text = ""
            reqs = ResourceNodeNotificationRequest.objects.filter(email=email.email)
            for req in reqs:
                previous_notifications = ResourceNodeNotification.objects.filter(request=req).order_by('-date_notified')
                if previous_notifications.count():
                    last_update = previous_notifications[0].date_notified
                else:
                    last_update = req.date_created
                
                new_resources = ResourceNodes.objects.filter(node=req.node, date_created__gt=last_update)
                if new_resources.count():
                    email_text = email_text + req.node.name + ' has new resources:\n'
                for nr in new_resources:
                    email_text = email_text + nr.resource.name + '\n'
                    # Save record of this relationship being notified via email
                    nt = ResourceNodeNotification()
                    nt.request = req
                    nt.resourceNodes = nr
                    nt.date_notified = datetime.utcnow()
                    nt.save()


            if len(email_text):
                send_mail("IEEE Technav new resource notification", email_text, settings.DEFAULT_FROM_EMAIL, [email.email])

