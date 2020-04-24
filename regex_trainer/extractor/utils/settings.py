# -*- coding:utf-8 -*-
# @Author: wmy
# @Time: 2019/12/4
# @Description:
import os
import sys
from pathlib import Path

EXTRACTOR_PATH = Path(__file__).parent.parent
XPATH_FILE_PATH = str(Path(EXTRACTOR_PATH).joinpath('static/xpath_pool.json'))
CACHES_TARGET_DIR = str(EXTRACTOR_PATH.parent.joinpath("caches"))

CONFIG_INI_BASE_DIR = EXTRACTOR_PATH.parent.joinpath("conf")

DEFAULT_FIELDS = [
    "title",
    "channel",
    "leadtitle",
    "subtitle",
    "publish_date",
    "source",
    "author",
    "editor",
    "video_url",
    'htmlcontent',
    'content',
    'origin_image_list'
]
