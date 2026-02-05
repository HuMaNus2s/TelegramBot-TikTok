import logging
from config.config import DEV_LOGS

if DEV_LOGS == True or DEV_LOGS.lower() in ["true", "yes", "ok", "0", 0]:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
else: 
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
log = logging.getLogger(__name__)