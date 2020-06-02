# -*- coding:utf-8 -*-
# @Author: zhu733756
# @Time: 2020/4/13
# @Description:
from datetime import datetime
import json
import os
import sys
import pathlib
import numpy as np

import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import Request, HtmlResponse
from scrapy.spiders import Rule
from .base_crawlspider import CrawlSpider
from scrapy.linkextractors import LinkExtractor
from ..extractor.total_extractor import SmartGuessExtractor

import random
from tldextract import tldextract
import codecs
import re
import json
from copy import copy
import uuid

MAX_ITEM_COUNT = 100
MAX_LINK_PERCENT = 0.5


class RegexTrainerSpider(CrawlSpider):
    name = 'regex_trainer'
    custom_settings = {
        'DEPTH_LIMIT': 3
    }

    def __init__(self, *args, **kwargs):
        super(RegexTrainerSpider, self).__init__(*args, **kwargs)
        kwargs = copy(kwargs)
        self.spider_name = kwargs.get("web_name", None)
        self.start_urls = self.keep_correct_type(
            kwargs.get("start_urls", None), "list")
        self.job_id = kwargs.get("_job", str(uuid.uuid1()))
        self.target_domain = None
        allowed_domains = self.get_allowed_domains(
            kwargs.get("allowed_domains", None) or self.start_urls[0])
        self.allowed_domains = self.keep_correct_type(allowed_domains, "list")
        self.domains_set = set()
        self.domain_url = self.get_domain_url()
        self.extractor = SmartGuessExtractor.from_config(
            config_name=self.spider_name)
        self.count = 0
        article_rule = kwargs.get("article_rule", ".*")
        deny_article_rule = article_rule if article_rule not in (
            ".*") else ".*s?html?.*"
        self.rules = (
            Rule(LinkExtractor(allow=(f'{article_rule}')),
                 callback='parse_article', follow=False),
            Rule(LinkExtractor(deny=(f'{deny_article_rule}')), follow=True),
        )
        self._compile_rules()
        kwargs_prints = ",".join(
            [key.replace("_", "") + '=' + value for key, value in kwargs.items()])
        self.logger.info(f'Spider kwargs: {kwargs_prints}')

    def keep_correct_type(self, values, needed="str"):
        if isinstance(values, str):
            match_list_type = re.search("\[.*\]", values)
            if match_list_type:
                try:
                    return json.loads(values)
                except json.JSONDecodeError:
                    pass
        return values if needed == "str" else [values]

    def set_allowed_domains(self, url):
        domain_val = tldextract.extract(url)
        if domain_val.domain == self.target_domain:
            domains = "{}.{}.{}".format(
                domain_val.subdomain, domain_val.domain, domain_val.suffix)
            self.domains_set.add(domains)

    def get_allowed_domains(self, start_url_or_domain):
        domain_val = tldextract.extract(start_url_or_domain)
        self.target_domain = domain_val.domain
        domains = "{}.{}".format(domain_val.domain, domain_val.suffix)
        return domains

    def get_domain_url(self):
        domain_val = tldextract.extract(self.start_urls[0])
        suffix = domain_val.suffix
        suffix_index = self.start_urls[0].index(suffix)
        suffix_length = len(suffix)
        return self.start_urls[0][:suffix_index + suffix_length]

    def _requests_to_follow(self, response):
        if not isinstance(response, HtmlResponse):
            return
        seen = set()
        for n, rule in enumerate(self._rules):
            links = [lnk for lnk in rule.link_extractor.extract_links(response)
                     if lnk not in seen]
            if links and rule.process_links:
                links = rule.process_links(links)
            # get samples
            links = np.random.choice(links, int(len(links) * MAX_LINK_PERCENT))
            for link in links:
                seen.add(link)
                r = self._build_request(n, link)
                try:
                    yield rule.process_request(r)
                except:
                    yield rule.process_request(r, response)

    def parse_article(self, response):
        if self.count > MAX_ITEM_COUNT:
            self.crawler.engine.close_spider(self, '抓取数量已达上限')
        self.count += 1
        # allowed domains
        self.set_allowed_domains(response.url)
        # add html
        self.extractor.add_html(response.body.decode())
        # get a sample
        try:
            content_infos = self.extractor.extract(clean_xpath=False)
            content_infos.update({"url": response.url})
            yield content_infos
        except Exception as e:
            print(f"采集报错:{e.args},url={response.url}")
