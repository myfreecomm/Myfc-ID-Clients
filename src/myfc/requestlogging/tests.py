# coding: UTF-8

import logging

from unittest import TestCase
from log_utils import logger
from mock import patch

__all__ = ['TestLogger']


class TestLogger(TestCase):

    @patch.object(logging.root, 'log')
    def test_logger_log(self, mock_log):
        obj = object()
        logger.log(logger.INFO, 'test', request=obj)

        self.assertEqual(mock_log.call_args, (
            (logger.INFO, '[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'info')
    def test_logger_info(self, mock_log):
        obj = object()
        logger.info('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'debug')
    def test_logger_debug(self, mock_log):
        obj = object()
        logger.debug('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'warning')
    def test_logger_warn(self, mock_log):
        obj = object()
        logger.warn('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'warning')
    def test_logger_warning(self, mock_log):
        obj = object()
        logger.warning('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'error')
    def test_logger_error(self, mock_log):
        obj = object()
        logger.error('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'critical')
    def test_logger_fatal(self, mock_log):
        obj = object()
        logger.fatal('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))


    @patch.object(logging.root, 'critical')
    def test_logger_critical(self, mock_log):
        obj = object()
        logger.critical('test', request=obj)

        self.assertEqual(mock_log.call_args, (
            ('[{0}] test'.format(id(obj)), ),
            { 'extra': {} },
        ))
