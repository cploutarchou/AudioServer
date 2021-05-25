import logging
import graypy

logger = logging.getLogger('AudioServer')
logger.setLevel(logging.DEBUG)

handler = graypy.GELFHTTPHandler('0.0.0.0', 12201)
logger.addHandler(handler)
