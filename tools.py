# -*- coding: utf8 -*-

import logging
from logging.handlers import RotatingFileHandler

# mapping for logging verbosity
verbosity_map = {
    'ERROR': logging.ERROR,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
}


def get_logger(logger_name, logfile, verbosity):
    log = logging.getLogger(logger_name)
    log.setLevel(verbosity_map.get(verbosity, logging.INFO))
    
    if logfile:
        handler = RotatingFileHandler(logfile, maxBytes=1024*1024, backupCount=2)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        log.addHandler(handler)
    
    if verbosity == 'INFO' or not logfile:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        log.addHandler(stream_handler)
    
    return log

