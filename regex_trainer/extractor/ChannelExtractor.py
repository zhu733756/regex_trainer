import re
from .utils.helper import iter_node, guess_total_xpath_from_node
from copy import copy
from .BaseExtractor import BaseExtractor


class ChannelExtractor(BaseExtractor):
    '''提取作者、编辑、来源等字段'''

    def __init__(self, element, xpath, pattern, guess_from_img_xpath, guess_from_title_xpath):
        self.element = element
        self.xpath = xpath
        self.pattern = pattern
        self.guess_from_img_xpath = guess_from_img_xpath
        self.guess_from_title_xpath = guess_from_title_xpath
        self.ignore_nodes = set()

    @classmethod
    def from_fields(cls, parser, element, guess_from_img_xpath=None, guess_from_title_xpath=None):
        pattern = parser.get("channel", "PATTERN")
        xpath = parser.get("channel", "XPATH")
        return cls(
            element=element,
            xpath=eval(xpath),
            pattern=eval(pattern),
            guess_from_img_xpath=guess_from_img_xpath,
            guess_from_title_xpath=guess_from_title_xpath
        )

    def extract_all_text_from_node(self, element):
        if not isinstance(element, list):
            element = [element]
        return "".join(["".join(n.xpath("string(.)")) for n in element]).strip("\n\t")

    def find_fath_nodes(self, node, deep=2):
        '''deep 遍历深度不超过deep'''
        c = 1
        while 1:
            if c > deep or not self.check_nodes(node=node):
                return False
            nparent = node.getparent()
            if nparent is not None:
                ct = "".join(nparent.xpath("string(.)"))
                if self.find_pattern(text=ct):
                    return True
            node = nparent
            c = c + 1

    def filter_channels(self, channel_tags):
        '''筛选具有相同祖先node的channel_tags，其他过滤，遍历深度两层'''
        nparent_nodes, filter_indexes = [], set()

        for index, t in enumerate(channel_tags):
            nparent = t.get("node").getparent()
            if nparent is not None:
                nparent_nodes.append((nparent, index))
                nnparent = nparent.getparent()
                if nnparent is None:
                    filter_indexes.add(index)
            else:
                filter_indexes.add(index)

        pop_index = []
        com_nparent_node = ""

        for i in range(len(nparent_nodes)):
            x = nparent_nodes[i][0]
            other = nparent_nodes[:i] + nparent_nodes[i + 1:]
            y = [t[0] for t in other]
            interation_y = set(x.getchildren()) & set(y)
            if x in y:
                com_nparent_node = x
            elif len(interation_y):
                com_nparent_node = list(interation_y)[0]
            elif x.getparent() in y:
                com_nparent_node = x.getparent()
            else:
                filter_indexes.add(nparent_nodes[i][1])
                pop_index.append(i)

        channel_tags = [c for i, c in enumerate(channel_tags)
                        if i not in filter_indexes]
        return com_nparent_node, channel_tags

    def extract_by_html_node(self, element):
        if not self.check_nodes(element):
            return []
        if element in self.ignore_nodes:
            return []

        c, channel_tags = [], []
        for n in iter_node(element):
            if n in self.ignore_nodes:
                continue
            channel_href = n.get("href")
            channel_name = re.sub("\s+", "", str(n.text)) if n.text else ''
            if channel_href and channel_name and n.tag == "a":
                if not self.find_fath_nodes(node=n):
                    continue
                channel_tags.append({
                    "node": n,
                    "href": channel_href,
                    "name": channel_name,
                })
            self.ignore_nodes.add(n)
        if channel_tags:
            com_nparent_node, filter_channels = self.filter_channels(
                channel_tags)
            if com_nparent_node == "":
                return dict(xpath="", value="", regex="")
            channel_infos, c = [], []
            for channel in filter_channels:
                c.append(channel.get("name"))
                channel_infos.append({
                    "channel_href": channel.get("href"),
                    "channel_name": channel.get("name"),
                    "channel_nav": ">".join(c)
                })
            return dict(
                xpath=guess_total_xpath_from_node(
                    node=com_nparent_node) + "//a",
                value=channel_infos,
                regex=""
            )
        return {}

    def check_nodes(self, node):
        if node.tag not in ("html", "head"):
            return True
        return False

    def from_guess_xpath(self, xpath):
        nodes = copy(self.element)
        # title或者img目标xpath内的node全部 忽略遍历
        for node in nodes.xpath(xpath):
            self.ignore_nodes.add(node)

        while 1:
            e_nodes = nodes.xpath(xpath)
            if not e_nodes:
                continue
            if not self.check_nodes(e_nodes[0]):
                break

            # 遍历tree树
            for e_node in e_nodes:
                for node in e_node.getchildren():
                    if node in self.ignore_nodes:
                        continue
                    ctext = self.extract_all_text_from_node(element=node)
                    if self.find_pattern(text=ctext):
                        ch = self.extract_by_html_node(node)
                        if ch:
                            return ch
                    self.ignore_nodes.add(node)

            xpath = xpath + "/.."

        return []

    def find_pattern(self, text):
        if not text:
            return False

        r = re.search(re.compile(self.pattern), text)
        if r:
            return True
        return False

    def extract_by_xpath(self):
        xpath = ''
        if isinstance(self.xpath, str):
            xpath = self.xpath
        if isinstance(self.xpath, list):
            for p in self.xpath:
                if p and self.element.xpath(p):
                    xpath = p
                    break
        if xpath:
            node = self.element.xpath(xpath)[0]
            return self.extract_by_html_node(node)
        return ''

    def extract(self):
        if self.xpath:
            rel = self.extract_by_xpath()
            if bool(rel):
                return rel

        guess_xpaths = [self.guess_from_title_xpath, self.guess_from_img_xpath]
        for xpath in guess_xpaths:
            if xpath:
                rel = self.from_guess_xpath(xpath)
                if bool(rel):
                    return rel
        else:
            return []
