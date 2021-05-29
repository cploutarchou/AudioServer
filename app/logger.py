import logging
import graypy

logger = logging.getLogger('AudioServer')
logger.setLevel(logging.DEBUG)

handler = graypy.GELFHTTPHandler('172.21.0.35', 12201)
logger.addHandler(handler)
