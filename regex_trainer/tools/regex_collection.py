from collections import defaultdict, OrderedDict
import re
from dateparser.date import DateDataParser

charaters = ["?", "&", "=", ".", "_", "+"]


class RegexCollection(object):

    buckets = {}  # 根据url节点数来存放

    def __init__(self, domains: str, prefix=None):
        '''
        keep: keep the first node;
        prefix: the prefix of the return regex,the default value is the domain value;
        '''
        self.domains = domains if not domains.endswith("/") else domains[:-1]
        self.prefix = prefix or self.domains

    def _pre_nodes(self, s: str) -> list:
        '''split and keep date format with one node'''
        return [n for n in s.split("/")[3:] if n]

    def add(self, s: str):
        """Add a string to this trie."""
        nodes = self._pre_nodes(s)
        length = len(nodes)
        char_length = len([i for i in charaters if i in s])
        char_bucket = self.buckets.setdefault(
            length, {}).setdefault(char_length, [None] * length)
        for i in range(length):
            if char_bucket[i] is None:
                char_bucket[i] = [nodes[i]]
            else:
                char_bucket[i].append(nodes[i])

    def longest_common_prefix(self, strs: list) -> str:
        '''
        获取字符串匹配最长前缀
        '''
        if len(strs) == 0:
            return ''
        min_string = min(strs)
        max_string = max(strs)
        index = 0
        for i in range(len(min_string)):
            if min_string[i] != max_string[i]:
                index = i
                break
        else:
            index = len(min_string)
        return min_string[:index]

    def regex_comps(self, strs: list) -> str:
        '''
        获取字符串列表的匹配正则通式
        '''
        # 获取最长匹配前缀
        prefix = self.longest_common_prefix(strs)
        # 获取最长匹配尾缀
        append = self.longest_common_prefix([s[::-1] for s in strs])
        prefix_length = len(prefix)
        append_length = len(append)
        if append_length > 0 and prefix_length + append_length < len(max(strs)):
            matches = "".join([s[prefix_length: -append_length] for s in strs])
        else:
            matches = "".join([s[prefix_length:] for s in strs])
        matches = "".join(set(matches))
        if bool(matches) == 0:
            return prefix
        c = ""
        for char in charaters:
            if char in matches:
                c += char
        temp1 = re.sub(f"[{c}\d]+", "", matches)
        temp2 = re.sub(f"[{c}\w]+", "", matches)
        alum = "\d" if len(temp1) == len(temp2) else "\w"
        if c:
            prefix += f'[{c}{alum}]+'
        else:
            prefix += f'{alum}+'
        return prefix + append[::-1]

    def extract(self, nums=5) -> list:
        '''
        return the top nums of the results
        nums:int
        '''
        res = []
        for key in self.buckets:
            char_bucket = self.buckets[key]
            if len(char_bucket) == 0:
                continue
            # 将item分成含有特殊字符与不含有特殊字符
            for char_length, char_values in char_bucket.items():
                nodes = []
                for item in char_values:
                    prefix_regex = self.regex_comps(item)
                    if prefix_regex == "":
                        prefix_regex += ".*"
                    nodes.append(prefix_regex)
                nodes = self.prefix + "/" + "/".join(nodes)
                if len(char_values) > 0:
                    res.append((nodes, key, char_length, len(char_values[0])))
        return sorted(res, key=lambda x: x[-1], reverse=True)[:nums]


def from_csv(path, encoding="utf-8"):
    import pandas as pd
    try:
        target = list(
            set(pd.read_csv(path, encoding=encoding).loc[:, "link"].values))
        start = "https" if target[0].startswith("https") else "http"
        t = RegexCollection(
            f"{start}://" + target[0].split("/")[2], prefix=".*")
        for link in target:
            t.add(link)
        else:
            return t.extract(nums=100)
    except Exception as e:
        print(e.args)


def from_txt(path):
    import codecs
    t = None
    file = codecs.open(path, "r")
    for r in file.readlines():
        line = r.strip()
        if line:
            if t is None:
                start = "https" if line.startswith("https") else "http"
                t = RegexCollection(f"{start}://" + line.split("/")[2])
            t.add(line)
    else:
        ans = t.extract()
        print(ans)
    file.close()


if __name__ == '__main__':
    t = RegexCollection("http://www.bjmy.gov.cn/", prefix=".*")
    t.add('http://www.bjmy.gov.cn/col/col129/index.html')
    t.add('http://www.bjmy.gov.cn/col/col3334/index.html')
    t.add('http://www.bjmy.gov.cn/art/2020/1/2/art_2052_6.html')
    t.add('http://www.bjmy.gov.cn/art/2020/1/2/art_2055_17.html')
    print(t.extract())
