import re
from lxml.html import HtmlElement
from datetime import datetime
from .BaseExtractor import BaseExtractor
from .utils.helper import guess_total_xpath_from_node


class TimeExtractor(BaseExtractor):

    def __init__(self, element, xpath, pattern):
        self.element = element
        self.xpath = xpath
        self.pattern = pattern

    @classmethod
    def from_fields(cls, parser, element: HtmlElement):
        pattern = parser.get("publish_date", "PATTERN")
        xpath = parser.get("publish_date", "XPATH")
        return cls(
            element=element,
            xpath=eval(xpath),
            pattern=eval(pattern)
        )

    def extract_by_xpath(self, xpath):
        d = self.element.xpath(xpath)
        if d:
            return d[0]
        return ''

    def guess_xpath(self, value):
        _xpath_letters = f"//*[contains(text(),\'{value}\')]"
        element_node = self.element.xpath(_xpath_letters)
        if len(element_node) == 0:
            return ''
        return f"string({guess_total_xpath_from_node(node=element_node[0])})"

    def to_date_field(self, time_str):
        if not time_str:
            return None
        try:
            time_str = time_str.replace('年', '-').replace('月', '-')\
                .replace('日', '').replace('/', '-').replace('\\', '-')

            # 2018-01-01 12:01:01
            pat1 = '\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}:\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y-%m-%d %H:%M:%S")

            # 2018-01-01 12:01
            pat1 = '\d{4}-\d{1,2}-\d{1,2} \d{2}:\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y-%m-%d %H:%M")

            # 2018-01-0112:01:01
            pat1 = '\d{4}-\d{1,2}-\d{1,2}\d{2}:\d{2}:\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y-%m-%d%H:%M:%S")

            # 2018-01-0112:01
            pat1 = '\d{4}-\d{1,2}-\d{1,2}\d{2}:\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y-%m-%d%H:%M")

            # 2018-01-01
            pat1 = '\d{4}-\d{1,2}-\d{1,2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y-%m-%d")

            # 20180101
            pat1 = '\d{4}\d{2}\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y%m%d")

            # 20180101
            pat1 = '\d{4}\d{2}\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y%m%d")

            # 20-03-2305:21
            pat1 = '\d{2}-\d{2}-\d{4}:\d{2}'
            time = ''.join(re.findall(pat1, time_str))
            if time:
                return datetime.strptime(time, "%Y%m%d")
        except ValueError as e:
            print('格式化时间出错: \n传入错误时间字符串为: {}'.format(time_str))

    def extract(self):
        if self.xpath:
            if isinstance(self.xpath, str):
                value = self.extract_by_xpath(self.xpath)
                if bool(value):
                    return {
                        "xpath": self.xpath,
                        "value": value,
                        "regex": ""
                    }
            elif isinstance(self.xpath, list):
                for xpath in self.xpath:
                    value = self.extract_by_xpath(xpath)
                    if value:
                        return {
                            "xpath": xpath,
                            "value": value,
                            "regex": ""
                        }

        rel = {
            "xpath": "",
            "value": "",
            "regex": ""
        }

        text = ''.join(self.element.xpath('//body//text()'))

        for dt in self.pattern:
            dt_obj = re.search(dt, text)
            if dt_obj:
                rel.update({
                    "xpath": self.guess_xpath(dt_obj.group(1)),
                    "value": str(self.to_date_field(dt_obj.group(1))),
                    "regex": dt
                })
                break

        return rel
