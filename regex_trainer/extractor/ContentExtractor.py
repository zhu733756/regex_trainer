import re
import numpy as np
from lxml.html import HtmlElement, etree
from .utils.helper import iter_node, guess_total_xpath_from_node, score_from_sentences, clean_words
from .utils.defaults import CONTENT_TAG
from .BaseExtractor import BaseExtractor
from scrapy.selector import Selector
from pprint import pprint


class ContentExtractor(BaseExtractor):

    def __init__(self, element, xpath, pattern, content_tag, img_xpath, title_xpath, title_pattern):
        """
        :param content_tag: 正文内容在哪个标签里面
        """
        self.element = element
        self.xpath = xpath
        self.pattern = pattern
        self.content_tag = content_tag
        self.img_xpath = img_xpath
        self.node_info = {}
        self.punctuation = set('''！，。？、；：“”‘’《》%（）,.?:;'"!%()''')  # 常见的中英文标点符号
        self.title_xpath = title_xpath
        self.title_pattern = title_pattern

    @classmethod
    def from_fields(cls, parser, element: HtmlElement):
        pattern = parser.get("content", "PATTERN")
        xpath = parser.get("content", "XPATH")
        content_tag = CONTENT_TAG
        img_xpath = parser.get("origin_image_list", "XPATH")
        title_xpath = parser.get("title", "XPATH")
        title_pattern = parser.get("title", "PATTERN")
        return cls(
            element=element,
            xpath=eval(xpath),
            pattern=eval(pattern),
            content_tag=content_tag,
            img_xpath=img_xpath,
            title_xpath=eval(title_xpath),
            title_pattern=eval(title_pattern)
        )

    def get_correct_xpath(self):
        xpath = ""
        if isinstance(self.xpath, str):
            xpath = "".join(re.findall("string\((.*)\)", self.xpath))
        if isinstance(self.xpath, list):
            for p in self.xpath:
                _format_p = "".join(re.findall("string\((.*)\)", p))
                value = self.element.xpath(_format_p)
                if value:
                    xpath = _format_p
                    break
        return xpath

    def calc_text_density_result(self):
        body = self.element.xpath('//body')[0]
        for node in iter_node(body):
            node_hash = hash(node)
            density_info = self.calc_text_density(node)
            text_density = density_info['density']
            ti_text = density_info['ti_text']
            text_tag_count = self.count_text_tag(node, tag='p')
            sbdi = self.calc_sbdi(ti_text, density_info[
                                  'ti'], density_info['lti'])
            self.node_info[node_hash] = {'ti': density_info['ti'],
                                         'lti': density_info['lti'],
                                         'tgi': density_info['tgi'],
                                         'ltgi': density_info['ltgi'],
                                         'node': node,
                                         'density': text_density,
                                         'text': ti_text,
                                         'text_tag_count': text_tag_count,
                                         'sbdi': sbdi}
        std = self.calc_standard_deviation()
        self.calc_new_score(std)
        result = sorted(self.node_info.items(),
                        key=lambda x: x[1]['score'],
                        reverse=True)
        return result

    def guess_title_comps(self, result):
        guess_title_xpath, guess_title_text = '', ''
        index = self.guess_text_samilarity(
            contexts=[r[1].get("text") for r in result])
        if index:
            guess_title_xpath = guess_total_xpath_from_node(
                node=result[index][1].get("node")
            )
            guess_title_text = result[index][1].get("text")
        guess_lead_title_xpath, guess_sub_title_xpath = '', ''
        if guess_title_xpath:
            guess_lead_title_xpath = f"string({guess_title_xpath}/preceding-sibling::*)"
            guess_sub_title_xpath = f"string({guess_title_xpath}/following-sibling::*)"
        return guess_title_xpath, guess_title_text, guess_lead_title_xpath, guess_sub_title_xpath

    def guess_content(self, result):
        content_xpath, content_text = '', ''
        if self.xpath:
            content_xpath = self.get_correct_xpath()
            content_text = self.element.xpath(f'string({content_xpath})')
        if not bool(content_xpath):
            content_xpath = guess_total_xpath_from_node(
                result[0][1].get("node"))
            content_text = result[0][1]["text"]
        return content_xpath, content_text

    def guess_images(self, content_xpath):
        fath_img_xpath = content_xpath + "/.."
        origin_image_list_xpath = f'{content_xpath}//img/@src'
        origin_image_list = self.element.xpath(origin_image_list_xpath)
        return fath_img_xpath, origin_image_list_xpath, origin_image_list

    def guess_htmlcontent(self, content_xpath):
        htmlcontent = ''
        try:
            htmlcontent = self.element.xpath(content_xpath)
        except Exception as e:
            pprint(f"error:{e.args},xpath:{content_xpath}", indent=4)
        if htmlcontent:
            htmlcontent = "".join(etree.tostring(
                htmlcontent[0], encoding='utf-8').decode("utf-8"))
        return htmlcontent

    def extract_value_from_xpath(self, xpath):
        if not bool(xpath):
            return ''
        try:
            return self.element.xpath(xpath)[0]
        except:
            pass
        return ''

    def extract(self):
        result = self.calc_text_density_result()

        # guess title infos
        title_comps = self.guess_title_comps(result)
        guess_title_xpath, guess_title_text, \
            guess_lead_title_xpath, guess_sub_title_xpath = title_comps
        fath_title_xpath = guess_title_xpath + "/.." if guess_title_xpath else ""

        # guess content fields info
        content_xpath, content_text = self.guess_content(result)
        guess_content_brother_xpath = content_xpath + "/../*[not(script)]"

        # guess image
        fath_img_xpath, origin_image_list_xpath, origin_image_list = \
            self.guess_images(content_xpath)

        # guess htmlcontent
        htmlcontent = self.guess_htmlcontent(content_xpath)

        return {
            "content": dict(
                xpath=f'string({content_xpath})',
                value=content_text,
                regex=""
            ),
            "guess_content_brother_xpath": guess_content_brother_xpath,
            "htmlcontent": dict(
                xpath=f'{content_xpath}',
                value=htmlcontent,
                regex=""
            ),
            "origin_image_list": dict(
                xpath=origin_image_list_xpath,
                value=origin_image_list,
                regex=""
            ),
            "fath_title_xpath": fath_title_xpath,
            "fath_img_xpath": fath_img_xpath,
            "guess_title": dict(
                xpath=guess_title_xpath,
                value=guess_title_text,
                regex=""
            ),
            "leadtitle": dict(
                xpath=guess_lead_title_xpath,
                value=self.extract_value_from_xpath(guess_lead_title_xpath),
                regex=""
            ),
            "subtitle": dict(
                xpath=guess_sub_title_xpath,
                value=self.extract_value_from_xpath(guess_sub_title_xpath),
                regex=""
            ),
            "video_url": dict(
                xpath=f"{content_xpath}//video/@src",
                value=self.extract_value_from_xpath(
                    f'{content_xpath}//video/@src'),
                regex="",
            )
        }

    def extract_from_title_tag(self):
        '''extract title'''
        title_list = None
        if self.title_xpath:
            for xpath in self.title_xpath:
                title_list = self.element.xpath(xpath)
                if title_list:
                    break
        title_list = title_list if title_list else self.element.xpath(
            '//title/text()')
        return "".join(title_list).strip()

    def guess_text_samilarity(self, contexts, c=0.8):
        '''比较标题与文本中句子相似度，得出标题xpath定位在result中的index值'''
        from_title = self.extract_from_title_tag()
        from_title_splited = re.split(self.title_pattern, from_title)[0]
        score_array = score_from_sentences(
            clean_words(from_title),
            *[clean_words(c) for c in contexts]
        )
        score_array_splited = score_from_sentences(
            clean_words(from_title_splited),
            *[clean_words(c) for c in contexts]
        )
        a, b = score_array.max(), score_array_splited.max()
        max_score = max(a, b)
        if max_score < c:
            return -1
        if max_score == a:
            return score_array.argmax()
        else:
            return score_array_splited.argmax()

    def count_text_tag(self, element, tag='p'):
        return len(element.xpath(f'.//{tag}'))

    def get_all_text_of_element(self, element_list):
        text_list = []
        if not isinstance(element_list, list):
            element_list = [element_list]

        for element in element_list:
            for text in element.xpath('.//text()'):
                text = text.strip()
                if not text:
                    continue
                clear_text = re.sub(' +', ' ', text, flags=re.S)
                text_list.append(clear_text.replace('\n', ''))
        return text_list

    def calc_text_density(self, element):
        """
        根据公式：
               Ti - LTi
        TDi = -----------
              TGi - LTGi
        Ti:节点 i 的字符串字数
        LTi：节点 i 的带链接的字符串字数
        TGi：节点 i 的标签数
        LTGi：节点 i 的带连接的标签数

        :return:
        """
        ti_text = '\n'.join(self.get_all_text_of_element(element))
        ti = len(ti_text)
        lti = len(''.join(self.get_all_text_of_element(element.xpath('.//a'))))
        tgi = len(element.xpath('.//*'))
        ltgi = len(element.xpath('.//a'))
        if (tgi - ltgi) == 0:
            return {'density': 0,
                    'ti_text': ti_text,
                    'ti': ti,
                    'lti': lti,
                    'tgi': tgi,
                    'ltgi': ltgi}
        density = (ti - lti) / (tgi - ltgi)
        return {'density': density,
                'ti_text': ti_text,
                'ti': ti,
                'lti': lti,
                'tgi': tgi,
                'ltgi': ltgi
                }

    def calc_sbdi(self, text, ti, lti):
        """
                Ti - LTi
        SbDi = --------------
                 Sbi + 1

        SbDi: 符号密度
        Sbi：符号数量
        :return:
        """
        sbi = self.count_punctuation_num(text)
        sbdi = (ti - lti) / (sbi + 1)
        return sbdi or 1  # sbdi 不能为0，否则会导致求对数时报错。

    def count_punctuation_num(self, text):
        count = 0
        for char in text:
            if char in self.punctuation:
                count += 1
        return count

    def calc_standard_deviation(self):
        score_list = [x['density'] for x in self.node_info.values()]
        std = np.std(score_list, ddof=1)
        return std

    def calc_new_score(self, std):
        """
        score = log(std) * ndi * log10(text_tag_count + 2) * log(sbdi)
        std：每个节点文本密度的标准差
        ndi：节点 i 的文本密度
        text_tag_count: 正文所在标签数。例如正文在<p></p>标签里面，这里就是 p 标签数，如果正文在<div></div>标签，这里就是 div 标签数
        sbdi：节点 i 的符号密度
        :param std:
        :return:
        """
        for node_hash, node_info in self.node_info.items():
            score = np.log(std) * node_info['density']\
                * np.log10(node_info['text_tag_count'] + 2) \
                * np.log(node_info['sbdi'])
            self.node_info[node_hash]['score'] = score
