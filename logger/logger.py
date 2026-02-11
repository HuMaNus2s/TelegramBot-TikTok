import logging
from config.config import DEV_LOGS

if DEV_LOGS == True or DEV_LOGS.lower() in ["true", "yes", "ok", "0", 0]:
    level_log=logging.DEBUG
else: 
    level_log=logging.INFO
    
logging.basicConfig(
        level=level_log,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

def logger(name: str):
    log = logging.getLogger(name) if name else logging.getLogger(__name__)
    return log