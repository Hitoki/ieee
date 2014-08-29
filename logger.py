#import threading
#import logging
#from django.conf import settings
#
#_LOCALS = threading.local()
#
#def get_logger():
#    logger = getattr(_LOCALS, 'logger', None)
#    if logger is not None:
#        return logger
#
#    # Create the logger
#    logger = logging.getLogger()
#    
#    # Add a file handler
#    handler = logging.FileHandler(settings.LOG_FILENAME)
#    #formatter = logging.Formatter('[%(asctime)s]%(levelname)-8s"%(message)s"',
#                                   '%Y-%m-%d %a %H:%M:%S')
#    #handler.setFormatter(formatter)
#    logger.addHandler(handler)
#    logger.setLevel(getattr(settings, 'LOG_LEVEL', logging.NOTSET))
#
#    # Add a console handler
#    if settings.LOG_CONSOLE:
#        logger.addHandler(logging.StreamHandler())
#
#    setattr(_LOCALS, 'logger', logger)
#    return logger
#
#def log(msg):
#    logger = get_logger()
#    logger.debug(msg)
#
