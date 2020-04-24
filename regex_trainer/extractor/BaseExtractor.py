
# -*- coding: utf-8 -*-
# @Time    : 2019/11/11 9:54
# @Author  : zhu733756
# @FileName: BaseExtractor.py

from abc import ABCMeta, abstractmethod
# from collections import namedtuple


class BaseExtractor(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @classmethod
    def from_fields(self, *args, **kwargs):
        pass

    @abstractmethod
    def extract(self):
        pass

    @abstractmethod
    def extract_by_xpath(self):
        pass

# extract_detail = namedtuple("extract_detail",["xpath","text"])
