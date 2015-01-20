from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.template import Context, loader
from django.contrib.sites.models import Site

from webapp.models.notification import ResourceAdditionNotificationRequest, \
    ResourceAdditionNotification
from webapp.models.resource import Resource, ResourceNodes, ResourceType
from webapp.models.node import Node

from webapp.models.society import NodeSocieties
from django.conf import settings

import logging

import csv


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


class Command(BaseCommand):
    def handle(self, *args, **options):
        # import ipdb; ipdb.set_trace()

        logger = logging.getLogger('process_conf_diff')
        logger.warn('Starting processing of file %s' % args[0])

        NEW_COUNT = 0
        NEW_MARKED_OLD_COUNT = 0
        UPDATED_COUNT = 0
        UPDATED_MARKED_NEW_COUNT = 0
        DELETED_COUNT = 0
        DELETED_MISSING_COUNT = 0

        with open(args[0], 'r') as f:
            csv_reader = csv.reader(f)
            lineno = -1
            for row in csv_reader:
                lineno += 1
                ieee_id = row[1]
                logger.warn("Found ieee_id: %s" % ieee_id)
                if row[0].startswith('conference') \
                        or row[0].startswith('Updated'):
                    try:
                        resource_type = ResourceType.objects.\
                            getFromName(ResourceType.CONFERENCE)
                        conf = Resource.objects.get(
                            ieee_id=ieee_id,
                            resource_type=resource_type,
                        )
                        if row[0].startswith('conference'):
                            logger.warn('Marked new but existing record found.'
                                        ' Updating existing record.')
                            UPDATED_MARKED_NEW_COUNT += 1
                        else:
                            UPDATED_COUNT += 1
                    except Resource.DoesNotExist:
                        conf = Resource()
                        conf.resource_type = ResourceType.objects.\
                            getFromName(ResourceType.CONFERENCE)
                        conf.ieee_id = ieee_id
                        if row[0].startswith('Updated'):
                            logger.warn('Marked updated but no existing record'
                                        ' found. Creating new record.')
                            NEW_MARKED_OLD_COUNT += 1
                        else:
                            NEW_COUNT += 1

                    conf.name = row[2]
                    conf.description = row[3]
                    conf.url = row[4]
                    conf.socieyt_abbrev = row[5]
                    conf.year = row[7]
                    # conf.standard_status = row[7]
                    # conf.standard_technical_committed = row[8]

                    conf.keywords = row[9].replace('|', ',')
                    conf.priority_to_tag = str2bool(row[10].lower())
                    conf.completed = str2bool(row[11].lower())
                    conf.conference_series = row[12]
                    conf.date = datetime.strptime(row[15], '%d-%b-%y')
                    conf.date_end = datetime.strptime(row[16], '%d-%b-%y')
                    conf.city = row[17]
                    conf.state_province = row[18]
                    conf.country = row[19]

                    conf.save()

                elif row[0].startswith('Deleted'):
                    try:
                        resource_type = ResourceType.objects.\
                            getFromName(ResourceType.CONFERENCE)
                        conf = Resource.objects.get(
                            ieee_id=ieee_id,
                            resource_type=resource_type,
                        )
                        conf.delete()
                        logger.warn('Conference deleted.')
                        DELETED_COUNT += 1
                    except Resource.DoesNotExist:
                        DELETED_MISSING_COUNT += 1
                else:
                    logger.warn("Undetermined action: line does not start with"
                                " 'conference, 'Updated', nor 'Deleted'. "
                                "Rows starts with: %s" % row[0])

            logger.warn("Processing complete.")
            logger.warn("NEW COUNT: %d" % NEW_COUNT)
            logger.warn("NEW COUNT (MARKED UPDATED): %d" %
                        NEW_MARKED_OLD_COUNT)
            logger.warn("UPDATED COUNT: %d" % UPDATED_COUNT)
            logger.warn("UPDATED COUNT (MARKED NEW): %d" %
                        UPDATED_MARKED_NEW_COUNT)
            logger.warn("DELETED COUNT: %d" % DELETED_COUNT)
            logger.warn("DELETED COUNT (MISSING): %d" % DELETED_MISSING_COUNT)
            logger.warn("")
