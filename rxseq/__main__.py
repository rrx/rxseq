from . import controllers
import logging

log = logging.getLogger(__name__)

def callback(event):
    log.info(event)

logging.basicConfig(level=logging.INFO, format='%(relativeCreated)6d %(thread)s %(name)s %(message)s')

controllers.start(callback)
