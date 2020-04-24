import re
from lxml.html import HtmlElement
from lxml.etree import HTML
from .BaseExtractor import BaseExtractor
from scrapy.http import TextResponse
from .utils.helper import guess_total_xpath_from_node


class AuthEditorSourceExtractor(BaseExtractor):
    '''提取作者、编辑、来源等字段'''

    def __init__(self, element, xpath, pattern):
        self.element = element
        self.xpath = xpath
        self.pattern = pattern

    @classmethod
    def from_fields(cls, parser, extract_field, element: HtmlElement):
        pattern = parser.get(extract_field, "PATTERN")
        xpath = parser.get(extract_field, "XPATH")
        return cls(
            element=element,
            xpath=eval(xpath),
            pattern=pattern
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

        text = '\n'.join(self.element.xpath('//body//text()'))

        rel = {
            "xpath": "",
            "value": "",
            "regex": ""
        }

        for pattern in eval(self.pattern):
            _obj = re.search(re.compile(pattern), text)
            if _obj:
                value = _obj.group(1)
                rel.update({
                    "xpath": self.guess_xpath(value),
                    "value": value.strip(),
                    "regex": pattern
                })
                break

        return rel
