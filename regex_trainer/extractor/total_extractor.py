# -*- coding: utf-8 -*-
# @Time    : 2019/10/10 16:01
# @Author  : zhu733756
# @FileName: gne.py

import json
import os
import pathlib
import sys

from .utils.helper import pre_parse, remove_noise_node

from .OtherExtractor import AuthEditorSourceExtractor
from .ContentExtractor import ContentExtractor
from .TimeExtractor import TimeExtractor
from .TitleExtractor import TitleExtractor
from .ChannelExtractor import ChannelExtractor
from .utils.downloader import download_rendered_url
from .utils.settings import CONFIG_INI_BASE_DIR, DEFAULT_FIELDS, XPATH_FILE_PATH
# from configParser import ConfParser
from lxml.html import HtmlElement
import pathlib
import chardet
try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser

import requests

from scrapy.selector import Selector


class XpathPoolingExtractor(object):

    def __init__(self, html, fields):
        self.html = html
        self.fields = fields
        self.xpath_pool = json.load(
            open(XPATH_FILE_PATH, "r", encoding="utf-8"))

    def read_field_xpath_pool(self, field):
        return self.xpath_pool.get(field, [])

    def generate_field_xpath(self, field):
        field_xpath_pool = self.read_field_xpath_pool(field)
        field_xpath = self.check_field_xpath(field, field_xpath_pool)
        return field_xpath

    def check_field_xpath(self, field, xpath_pool):
        response = Selector(text=self.html)
        tmp_data = []
        for xpath in xpath_pool:
            try:
                ret = ''.join(response.xpath(xpath).extract()).strip()
            except:
                # todo 删除xpath
                ret = ''
            if ret:
                tmp_data.append({
                    "xpath": xpath,
                    "value": ret,
                    "regex": ""
                })
        return tmp_data

    @classmethod
    def from_url_sample(cls, project, spider, sample, script=None, fields=None):
        '''获取html对应的url'''
        ret = download_rendered_url(
            spider=spider, sample=sample, script=script)
        html = ret.get("content")
        query_fields = fields if fields else DEFAULT_FIELDS
        return cls(html=html, fields=query_fields)

    def clean(self, result):
        data = {}
        if result:
            for key in self.fields:
                kl = result.get(key, {})
                if kl:
                    del kl["value"]
                    data[key] = kl
        return data

    def extract(self, clean_xpath=True):
        xpath_dict = {}
        for field in self.fields:
            data = self.generate_field_xpath(field)
            xpath_dict[field] = data
        if clean_xpath:
            xpath_dict = self.clean(xpath_dict)
        return xpath_dict

    def get_sample_values(self):
        xpath_dict = {}
        for field in self.fields:
            data = self.generate_field_xpath(field)
            xpath_dict[field] = data.get("value")
        return xpath_dict


class SmartGuessExtractor(object):

    def __init__(self, parser, config_name, **kwargs):
        self.element = None
        self.parser = parser
        self.config_name = config_name
        self.fields = kwargs.get("fields") or DEFAULT_FIELDS
        self.noise_node_list = eval(
            self.parser.get('noise_node', 'noise_node_xpath_list'))
        self.content_infos = None

    def _init_single_extractor(self, extractor, *args, **kwargs):
        if self.element is None:
            raise ValueError(
                "please add html or url,you can use add_html or add_url_sample")
        return extractor.from_fields(
            parser=self.parser,
            element=self.element,
            *args,
            **kwargs
        )

    def _init_all_extractor(self):
        self.content_extractor = self._init_single_extractor(
            extractor=ContentExtractor
        )
        # keep content xpath
        self.content_infos = self._start_guess_content()
        self.author_extractor = self._init_single_extractor(
            extractor=AuthEditorSourceExtractor,
            extract_field="author"
        )
        self.editor_extractor = self._init_single_extractor(
            extractor=AuthEditorSourceExtractor,
            extract_field="editor"
        )
        self.source_extractor = self._init_single_extractor(
            extractor=AuthEditorSourceExtractor,
            extract_field="source"
        )
        self.publish_date_extractor = self._init_single_extractor(
            extractor=TimeExtractor
        )
        self.title_extractor = self._init_single_extractor(
            extractor=TitleExtractor,
            guess_from_title=self.content_infos.get("guess_title")
        )
        self.channel_extractor = self._init_single_extractor(
            extractor=ChannelExtractor,
            guess_from_img_xpath=self.content_infos.get("fath_img_xpath"),
            guess_from_title_xpath=self.content_infos.get("fath_title_xpath")
        )

    def add_html(self, html):
        html = pre_parse(html)
        html = remove_noise_node(html, self.noise_node_list)
        self.element = html
        self._init_all_extractor()

    def add_url_sample(self, sample, method="no-render", script=None, keep_cache=True):
        html = ""
        if method == "render":
            ret = download_rendered_url(
                spider=self.config_name, sample=sample, script=script, keep_cache=keep_cache)
            html = ret.get("content")
        else:
            headers = {
                "USER_AGENT": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.117 Safari/537.36'}
            resp = requests.get(sample, headers=headers)
            if resp.status_code == 200:
                html = resp.content
                charset = chardet.detect(html).get("encoding", "utf-8")
                try:
                    html = html.decode(charset, "ignore")
                except:
                    html = resp.text
        if html:
            self.add_html(html)
        else:
            print("download err")

    @classmethod
    def from_config(cls, config_name="website", **kwargs):
        '''handle scrapy response'''
        base_dir = CONFIG_INI_BASE_DIR
        config_path = base_dir.joinpath(f"{config_name}.ini")
        if not pathlib.Path(config_path).exists() or kwargs.pop("retraining", False):
            config_path = base_dir.joinpath("website.ini")
        parser = ConfigParser.RawConfigParser()
        parser.read(config_path, encoding="utf-8")
        return cls(
            parser=parser,
            config_name=config_name,
            kwargs=kwargs
        )

    def _start_guess_content(self):
        ''' the content extractor must run before othor extractors'''
        return self.content_extractor.extract()

    def clean(self, result):
        data = {}
        if result:
            for key in self.fields:
                kl = result.get(key, {})
                if kl:
                    del kl["value"]
                    data[key] = kl
        return data

    def extract(self, clean_xpath=True):
        '''
        some extractors refers to the poperty of content_infos:
        :return:
        '''
        ret = {}
        for field in self.fields:
            if field in ["content", "origin_image_list", "video_url",
                         "htmlcontent", "leadtitle", "subtitle"]:
                ret.update({field: self.content_infos.get(field, '')})
                continue
            func = getattr(self, f"{field}_extractor", None)
            func_results = func.extract() if func else ""
            ret.update({field: func_results})
        if clean_xpath:
            ret = self.clean(ret)
        return ret

    def get_sample_values(self):
        ret = {}
        for field in self.fields:
            if field in ["content", "origin_image_list", "video_url",
                         "htmlcontent", "leadtitle", "subtitle"]:
                value = self.content_infos.get(field, '').get("value", '')
                ret.update({field: value})
                continue
            func = getattr(self, f"{field}_extractor", None)
            func_results = func.extract() if func else {}
            value = func_results.get(field, '').get("value", '')
            ret.update({field: value})
        return ret

if __name__ == "__main__":

    sample = 'http://www.hzbwb.gov.cn/hzsqxsbbdt/104981.jhtml'
    extractor = SmartGuessExtractor.from_config(config_name="people")
    extractor.add_url_sample(sample=sample, method="no-render")
    result = extractor.extract()
    print(f'>>>>>>>>>>>>>{sample}>>>>>>>>>>>>>')
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print('<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<')
