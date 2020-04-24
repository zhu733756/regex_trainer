from scrapy import signals

# 需要用到的包
import re
from scrapy.exceptions import IgnoreRequest
import logging
from datetime import datetime, timedelta


class UrlDateFilterMiddleware(object):
    """根据url中的日期进行过滤"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # 添加时间过滤
        ret = self.filter_date(request.url)
        if ret:
            raise IgnoreRequest('file url filter')
        else:
            return None

    def spider_opened(self, spider):
        spider.logger.info('UrlDateFilterMiddleware opened: %s' % spider.name)

    def filter_date(self, url):
        url_date_regex_map = [
            {'url_regex': r'/(\d{4}-\d{1,2}-\d{1,2})/',
             'date_format': '%Y-%m-%d', 'type': 'day'},
            {'url_regex': r'/(\d{4}-\d{1,2}/\d{1,2})/',
             'date_format': '%Y-%m/%d', 'type': 'day'},
            {'url_regex': r'/(\d{4}/\d{1,2}-\d{1,2})/',
             'date_format': '%Y/%m-%d', 'type': 'day'},
            {'url_regex': r'/(\d{4}/\d{1,2}/\d{1,2})/',
             'date_format': '%Y/%m/%d', 'type': 'day'},
            {'url_regex': r'/(\d{6}/\d{1,2})/',
             'date_format': '%Y%m/%d', 'type': 'day'},
            {'url_regex': r'/(\d{4}/\d{4})/',
             'date_format': '%Y/%m%d', 'type': 'day'},
            {'url_regex': r'/(\d{6}-\d{2})/',
             'date_format': '%Y%m-%d', 'type': 'day'},
            {'url_regex': r'/\d{6}/t(\d{8})_',
             'date_format': '%Y%m%d', 'type': 'day'},
            {'url_regex': r'/(\d{8})/',
             'date_format': '%Y%m%d', 'type': 'day'},
            {'url_regex': r'/(\d{6})/', 'date_format': '%Y%m',
             'type': 'month'},
        ]
        for i in url_date_regex_map:
            part = re.compile(i.get('url_regex'))
            result = part.search(url)
            if result:
                try:
                    date = result.group(1)
                    date = datetime.strptime(date, i.get('date_format'))
                except ValueError as e:
                    logging.warning('url 日期匹配不正确')
                    continue

                if (datetime.today() - date).days <= 365:
                    # 文章在一年中
                    return False
                else:
                    # 时间不在一年中
                    return True
        else:
            # 没匹配到或者不在日期范围类退出
            return False


# 中间件代码
class UrlTextFilterMiddleware(object):
    """过滤多余请求"""

    def process_request(self, request, spider):
        # 关键字
        black_set = {'信箱', '站点地图', '末页', '关于我们', '版权声明', '浏览建议', '关于', '通知公告', '上一页',
                     '广告', '友情链接', '声明', '隐私保护', '留言', '网站地图', '通知', '公告', '法律声明', '网站致谢',
                     '天气', '在线留言', '天气预报', '网站声明', '联系我们', '法律责任', '广告合作', '更正',
                     '下一页', '详情', '尾页', '上页', '下页', '尾页'}
        link_text = request.meta.get('link_text', '')
        if link_text in black_set or link_text.isdigit():
            raise IgnoreRequest('file url filter')
        else:
            return None


# 中间件代码
class UrlFilterMiddleware(object):
    """url filter middleware written by fcj"""

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        from urllib.parse import urlsplit  # 局部区域引用包
        black_set = {  # 关键字
            'pdf', 'doc', 'jpg', 'png', 'xls', 'docx', 'gif', 'csv',
            'PDF', 'DOC', 'JPG', 'PNG', 'XLS', 'DOCX', 'GIF', 'CSV'
        }

        split_result = urlsplit(url=request.url).path
        # 使用urlsplit切割url,并最后得到path,path一般都包含了关键字.
        split_set = set(re.split(r'[/_.-]', split_result))
        # 再使用正则表达式,切割字符串,得到一个字符串列表,并set.
        intersection = split_set & black_set
        # set求和,若结果的set长度大于0,则两个set间存在相同元素.这一步主要是避免迭代寻找共同元素.
        if len(intersection) > 0:
            raise IgnoreRequest('file url filter')
            # 当有共同元素的时候,则证明url里有关键字,抛出忽略请求的异常即可.
            # 官文对这个异常的描述:This exception can be raised by the Scheduler or
            # any downloader middleware to indicate that the request should be
            # ignored.
        else:
            return None
            # 当返回None值时,爬虫会继续对request做处理.

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WebsiteSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WebsiteDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
