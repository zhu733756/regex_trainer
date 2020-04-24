# Obey robots.txt rules
ROBOTSTXT_OBEY = False
SPIDER_MODULES = ['regex_trainer.spiders']

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 1

DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 30

# USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'

DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.109 Safari/537.36'
}

ITEM_PIPELINES = {
    'regex_trainer.pipelines.regex_spider_pipelines.RegexSpiderPipeline': 200,
}

MYSQL_HOST = '127.0.0.1'
MYSQL_PORT = 3306
MYSQL_DATABASE = '$news_crawler'
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'root123'

# custom settings


DOWNLOADER_MIDDLEWARES = {
    'regex_trainer.middlewares.regex_spider_middlewares.WebsiteDownloaderMiddleware': 543,
    'regex_trainer.middlewares.regex_spider_middlewares.UrlTextFilterMiddleware': 345,
    'regex_trainer.middlewares.regex_spider_middlewares.UrlDateFilterMiddleware': 435,
}

import pathlib
import os

project_path = pathlib.Path(__file__).parent
CACHES_TARGET_DIR = project_path.joinpath("caches")
CONFIG_INI_BASE_DIR = project_path.joinpath("conf")

LOG_LEVEL = 'DEBUG'
