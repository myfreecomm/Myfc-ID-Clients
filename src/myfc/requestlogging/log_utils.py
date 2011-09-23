#coding: UTF-8


import logging

__all__ = ['logger']


class RequestAdapter(logging.LoggerAdapter):

    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARN = logging.WARN
    WARNING = logging.WARNING
    CRITICAL = logging.CRITICAL
    FATAL = logging.FATAL

    def process(self, msg, kwargs):
        if 'request' in kwargs:
            request_id = id(kwargs.pop('request'))
            msg = u'[{0}] {1}'.format(request_id, msg)

        return logging.LoggerAdapter.process(self, msg, kwargs)

    def fatal(self, msg, *args, **kwargs):
        self.critical(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self.warning(msg, *args, **kwargs)


logger = RequestAdapter(logging.getLogger(), {})
