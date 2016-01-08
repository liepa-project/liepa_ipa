# -*- coding: utf-8 -*-
# vim: set fileencoding=utf-8

import os
import sys
from utils import get_dir, makedirs
import logging
import logging.config


def get_log_dir():
    logdir = os.path.join(get_dir(__file__), 'log')
    makedirs(logdir)
    return logdir

def get(name):
    return logging.getLogger(name)


logconfig = {
    "version": 1,
    "formatters": {
        "console": {"format": "%(levelname)-7s %(message)s"},
        "logfile": {"format": "%(asctime)s - %(name)s - %(levelname)-7s - %(message)s"}
        },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": logging.DEBUG,
            "stream": "ext://sys.stderr",
            "formatter": "console"
            },
        "logfile": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": logging.DEBUG,
            "formatter": "logfile",
            "filename": os.path.join(get_log_dir(), "ipa.log"),
            "maxBytes": 1048576,
            "backupCount": 3,
            "encoding": "utf8"
            }
        },
     "root": {
        "level": logging.DEBUG,
        "handlers": ["console", "logfile"]}
    }

logging.config.dictConfig(logconfig)
