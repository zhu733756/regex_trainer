import re
import os
import json
import hashlib
import logging
from datetime import datetime
import base64
from scrapy.http import Request
from scrapy.utils.python import to_bytes
from scrapy.exceptions import DropItem
from twisted.enterprise import adbapi
import pymysql
import codecs
import pathlib
from collections import namedtuple
from ..tools.regex_collection import RegexCollection
from scrapy import Item, Field
from copy import copy
import re


class CoreWebsiteConsumer(Item):
    web_name = Field()
    start_urls = Field()
    status = Field()
    version = Field()
    allowed_domains = Field()
    article_regex = Field()
    job_id = Field()
    updated_at = Field()


class CoreWebXpathConfigItem(Item):
    web_name = Field()
    job_id = Field()
    version = Field()
    config = Field()
    sample = Field()
    sample_values = Field()
    created_at = Field()

MYSQL_TABLE_MAPPING = [{
    "table": "core_website_trainer_consumer",
    "item": "CoreWebsiteConsumer"
}, {
    "table": "core_website_xpath_config",
    "item": "CoreWebXpathConfigItem"
}]


class RegexSpiderPipeline(object):

    def __init__(self, host, database, user, password, port,
                 table_mapping, caches_target_dir, config_path):
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.table_mapping = table_mapping
        self.dbpool = None
        self.caches_target_dir = caches_target_dir
        self.config_path = config_path

    @classmethod
    def from_crawler(cls, crawler):
        settings = crawler.spider.settings
        return cls(
            host=settings.get('MYSQL_HOST'),
            database=settings.get('MYSQL_DATABASE'),
            user=settings.get('MYSQL_USER'),
            password=settings.get('MYSQL_PASSWORD'),
            port=settings.get('MYSQL_PORT'),
            table_mapping=settings.get(
                'MYSQL_TABLE_MAPPING', MYSQL_TABLE_MAPPING),
            caches_target_dir=settings.get(
                "CACHES_TARGET_DIR"),
            config_path=settings.get(
                "CONFIG_INI_BASE_DIR"),
        )

    def open_spider(self, spider):
        self.dbpool = adbapi.ConnectionPool(
            'pymysql', host=self.host, user=self.user,
            passwd=self.password, db=self.database,
            charset='utf8mb4', cursorclass=pymysql.cursors.DictCursor, use_unicode=True)
        self.spider_dirpath = pathlib.Path(self.caches_target_dir).joinpath(
            f"{spider.spider_name}")
        if not pathlib.Path(self.spider_dirpath).exists():
            os.makedirs(self.spider_dirpath)
        self.target_filepath = str(
            self.spider_dirpath.joinpath(f"{spider.target_domain.replace('.','_')}.json"))
        self.target_link_filepath = str(
            self.spider_dirpath.joinpath(f"links.json"))
        self.config_filepath = str(self.config_path.joinpath(
            f"{spider.spider_name}.ini"))

        self.xpath_file = codecs.open(
            self.target_filepath, 'a+', encoding='utf-8')
        self.regex_collection = RegexCollection(spider.domain_url, prefix=".*")
        self.logger = spider.logger
        self.job_id = spider.job_id
        self.import_fields = ["channel", "title", "content", "publish_date"]

    def process_item(self, item, spider):
        if not item.get("content") or not item.get("title"):
            raise DropItem("content为空")
        # 当重要字段中有两个以上字段没有采集到将此条item过滤
        import_counts = [bool(item.get(f, {}).get("value", None))
                         for f in self.import_fields].count(True)
        if import_counts <= 2:
            raise DropItem("重要字段缺失2个以上")
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.xpath_file.write(line)
        self.regex_collection.add(item.get("url"))
        # self.dbpool.runInteraction(self.save_item, item)
        return item

    def close_spider(self, spider):
        self.xpath_file.close()
        # get article rule
        article_rule = self._extract_regex(spider.spider_name)
        # filter by article rule
        useful_content = self._filter_xpath_results(article_rule)
        # keep useful links
        self._keep_links(useful_content)
        # get a sample
        sample = json.loads(useful_content[0]).get("url") \
            if len(useful_content) > 0 else ''
        # extract it
        sample_values = json.loads(useful_content[0])
        # extract common xpath
        self._extract_common_xpath(spider.extractor, useful_content)
        version, config_infos = self._saveAndreturn(spider.extractor)
        item1 = self._gen_spider_infos(spider, version, article_rule)
        item2 = self._gen_spider_xpath_infos(
            spider.spider_name, version, config_infos, sample, sample_values)
        # save item
        for item in [item1, item2]:
            self.dbpool.runInteraction(self.save_item, item)
        self.logger.info('finish crawl: %s' % spider.spider_name)

    def _filter_xpath_results(self, article_rule):
        '''根据最佳匹配rule反向筛选link'''
        content = codecs.open(self.target_filepath, "r",
                              encoding="utf-8").read().split("\n")
        return list(filter(lambda x: x and re.search(article_rule, json.loads(x).get("url", "")), content))

    def _keep_links(self, content):
        article_links_file = codecs.open(
            self.target_link_filepath, "w", encoding='utf-8')
        for c in content:
            if c:
                line = json.loads(c).get("url")
                article_links_file.write(line + "\n")
        article_links_file.close()

    def _extract_regex(self, spider_name):
        '''extract regex'''
        article_regex = self.regex_collection.extract()
        article_regex = article_regex[0][0] if len(article_regex) > 0 else ''
        print('{} article_regex is {}'.format(spider_name, article_regex))
        return article_regex

    def _extract_common_xpath(self, extractor, content):
        '''extract common xpath'''
        def _write_config(extractor, field, tp, field_set):
            if field_set and field in extractor.parser.sections():
                extractor.parser.set(field, tp, list(field_set))

        fields = extractor.fields
        for s in content:
            if not s:
                continue
            try:
                data = json.loads(s)
                field_set = {}
                for field in fields:
                    rel = data.get(field, {})
                    if not bool(rel):
                        continue
                    xpath = rel.get("xpath", "")
                    regex = rel.get("regex", "")
                    if xpath:
                        field_set.setdefault("xpath", set()).add(xpath)
                    if regex:
                        field_set.setdefault("regex", set()).add(regex)

                if field_set.get("xpath", None):
                    _write_config(
                        extractor, field, "XPATH", field_set["xpath"])
                if field_set.get("regex", None):
                    _write_config(
                        extractor, field, "REGEX", field_set["regex"])
            except Exception as e:
                print(e.args)

    def _saveAndreturn(self, extractor):
        '''save config and returns a tuple'''
        version = extractor.parser.getint("version", "version") + 1
        extractor.parser.set("version", "version", version)
        with open(self.config_filepath, "w", encoding="utf-8") as file:
            extractor.parser.write(file)
        config_dict = copy(dict(extractor.parser._sections))
        del config_dict["version"]
        config_content = json.dumps(config_dict)
        return version, config_content

    def get_sample_values(self, url, extractor):
        import requests
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'en',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            body = response.text
            extractor.add_html(body)
            return extractor.extract(clean_xpath=True)
        return {}

    def _gen_spider_xpath_infos(self, name, version, content, sample, sample_values):
        item = CoreWebXpathConfigItem()
        item["web_name"] = name
        item["version"] = int(version)
        item["job_id"] = self.job_id
        item["config"] = content
        item["sample"] = sample
        item["sample_values"] = json.dumps(sample_values)
        item["created_at"] = datetime.now()
        return item

    def _gen_spider_infos(self, spider, version, article_rule):
        item = CoreWebsiteConsumer()
        for key in item.fields.keys():
            if key == "article_regex":
                value = article_rule
            elif key == "web_name":
                value = spider.spider_name
            else:
                value = getattr(spider, key, "")
                if isinstance(value, (tuple, list)):
                    value = json.dumps(list(value))
            item[key] = value
        item["updated_at"] = datetime.now()
        item["version"] = version
        item["status"] = 1
        return item

    def save_item(self, cur, item):
        self.logger.debug("save item:" + str(item.get("url")))
        for table_mapping in self.table_mapping:
            if type(item).__name__ == table_mapping.get('item'):
                table = table_mapping.get('table')
                key_list = list(item.keys())
                sql = 'insert into {table} (`{key}`) values ({value}) on DUPLICATE key update {update}'.format(
                    table=table,
                    key='`, `'.join(key_list),
                    value=', '.join(['%s'] * len(key_list)),
                    update=', '.join(['`{}`=%s'.format(i) for i in key_list])
                )
                value = tuple(item.get(key, '') for key in key_list) * 2
                try:
                    cur.execute(sql, value)
                except Exception as e:
                    print('mysql报错信息: {}表出现问题\n问题URL为：{}\n报错信息为：{}\n'.format(
                        table, item.get('url', '没有url'), e))
