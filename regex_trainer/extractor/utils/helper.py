# -*- coding: utf-8 -*-
# @Time    : 2019/10/10 10:28
# @Author  : zhu733756
# @FileName: __ini__.py

from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import jieba
from lxml.html import fromstring, HtmlElement
from lxml.html import etree
import re
from .defaults import *
import numpy as np
from .defaults import BETTER_CONTENT_NODE_REMOVE_TAG, USEFUL_ATTR


def clean_words(sentence):
    return " ".join(jieba.cut(sentence=sentence, cut_all=False))


def score_from_sentences(v1, *args):
    '''get scores from different sentences'''
    if len(args) < 1:
        raise ValueError("the number of sentences cannot be one")

    vocab = {}
    for word in v1.split():
        vocab[word] = 0
    for o in args:
        for word in o.split():
            vocab[word] = 0

    if len(list(vocab.keys())) == 0:
        return np.array([-1])

    cv = CountVectorizer(vocabulary=vocab.keys())
    sentenceVector = cv.fit_transform([v1])
    docVector = cv.fit_transform(args)
    return cosine_similarity(sentenceVector, docVector)[0]


def normalize_node(element: HtmlElement):
    for node in iter_node(element):
        if node.tag.lower() in USELESS_TAG:
            remove_node(node)

        # inspired by readability.
        if node.tag.lower() in TAGS_CAN_BE_REMOVE_IF_EMPTY and is_empty_element(node):
            remove_node(node)

        # p 标签下面的 span 标签中的文字，可以合并到 p 标签中
        if node.tag.lower() == 'p':
            etree.strip_tags(node, 'span')
            etree.strip_tags(node, 'strong')

        # if a div tag does not contain any sub node, it could be converted to
        # p node.
        if node.tag.lower() == 'div' and not node.getchildren():
            node.tag = 'p'

        if node.tag.lower() == 'span' and not node.getchildren():
            node.tag = 'p'

        class_name = node.get('class')
        if class_name:
            for attribute in USELESS_ATTR:
                if attribute in class_name:
                    remove_node(node)
                    break


def pre_parse(html):
    html = re.sub('</?br.*?>', '', html)
    html = re.sub('<!--.*?-->', '', html)  # 去除注释
    element = fromstring(html)
    normalize_node(element)
    return element


def remove_noise_node(element, noise_xpath_list):
    if not noise_xpath_list:
        return
    for noise_xpath in noise_xpath_list:
        nodes = element.xpath(noise_xpath)
        for node in nodes:
            remove_node(node)
    return element


def iter_node(element: HtmlElement):
    yield element
    for sub_element in element:
        if isinstance(sub_element, HtmlElement):
            yield from iter_node(sub_element)


def remove_node(node: HtmlElement):
    """
    this is a in-place operation, not necessary to return
    :param node:
    :return:
    """
    parent = node.getparent()
    if parent is not None:
        parent.remove(node)


def is_empty_element(node: HtmlElement):
    return not node.getchildren() and not node.text


def guess_xpath_of_cur_node(node):
    '''
    guess xpath from node
    '''
    class_property = node.get("class")
    id_property = node.get("id")
    if class_property is not None:
        return f'{node.tag}[@class="{class_property}"]'
    if id_property is not None:
        return f'{node.tag}[@id="{id_property}"]'
    # attributes = node.classes._attributes
    # if attributes:
    #     k,v = attributes.items()[0]
    #     if k in USEFUL_ATTR:
    #         return f'{node.tag}[@{k}="{v}"]'
    return f'{node.tag}'


def guess_total_xpath_from_node(node):
    '''根据node获取xpath'''
    while 1:
        if node.tag not in BETTER_CONTENT_NODE_REMOVE_TAG\
                or node.tag == "body":
            break
        node = node.getparent()

    total_xpath = ''
    switch = False
    count = 0

    while 1:
        current_xpath = guess_xpath_of_cur_node(node)
        index = get_cnode_index(node.getparent(), node)

        if re.search("@", current_xpath) or index == 0:
            total_xpath = f'/{current_xpath}' + total_xpath
            if re.search("@id|@class", current_xpath):
                switch = True
        else:
            total_xpath = f'/{current_xpath}[{index+1}]' + total_xpath

        if switch and count > 1:
            break
        if node.getparent().tag in ("body", "html"):
            break
        node = node.getparent()
        count += 1
    return f'/{total_xpath}'


def get_cnode_index(pnode, cnode):
    filter_pnode = []
    for index, n in enumerate(pnode.getchildren()):
        if n.tag == cnode.tag:
            filter_pnode.append(n)
    return filter_pnode.index(cnode)

if __name__ == '__main__':
    s1 = "各民族共建美好家园共创美好未来--观点--人民网 "
    s4 = "各民族共建美好家园共创美好未来--观点--人民网 "
    s2 = '各民族共建美好家园共创美好未来'
    s3 = '在全国民族团结进步表彰大会上，习近平总书记全面分析当前我国民族工作面临的形势，明确提出新时代推动民族团结进步事业的总体要求和工作重点，擘画了'
    print(score_from_sentences(clean_words(s1), clean_words(
        s2), clean_words(s3), clean_words(s4)))
