# -*- coding: utf-8 -*-
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem, RawHtmlItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


class OabtSpider(BaseSpider):
    version = '1.0.0'
    name = 'oabt'
    allowed_domains = ['oabt004.com']
    start_urls = [
        'http://oabt004.com/index/index?cid=1',
        'http://oabt004.com/index/index?cid=6',
        'http://oabt004.com/index/index?cid=25',
        'http://oabt004.com/index/index?cid=21',
        'http://oabt004.com/index/index?cid=26',
        'http://oabt004.com/index/index?cid=28',
        'http://oabt004.com/index/index?cid=3',
        'http://oabt004.com/index/index?cid=18',
        'http://oabt004.com/index/index?cid=23',
        'http://oabt004.com/index/index?cid=5',
        'http://oabt004.com/index/index?cid=29',
    ]

    deep_start_urls = [
        'http://oabt004.com/index/index?cid=1',
        'http://oabt004.com/index/index?cid=6',
        'http://oabt004.com/index/index?cid=25',
        'http://oabt004.com/index/index?cid=21',
        'http://oabt004.com/index/index?cid=26',
        'http://oabt004.com/index/index?cid=28',
        'http://oabt004.com/index/index?cid=3',
        'http://oabt004.com/index/index?cid=18',
        'http://oabt004.com/index/index?cid=23',
        'http://oabt004.com/index/index?cid=5',
        'http://oabt004.com/index/index?cid=29',
    ]

    rules = (
        Rule(LinkExtractor(allow='index/index/cid/\d+/p/(1|2|3|4|5)', ), follow=True, callback='handle_list'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='index/index/cid/\d+/p/\d+', ), follow=True, callback='handle_list'),
    )

    def parse_start_url(self, response):
        return RawHtmlItem(url=response.url, html=response.text, task=self.settings.get('APP_TASK'),
                           version=self.version, timestamp=math.floor(time.time()))

    def handle_list(self, response: Response) -> RawHtmlItem:
        return RawHtmlItem(url=response.url, html=response.text, task=self.settings.get('APP_TASK'),
                           version=self.version, timestamp=math.floor(time.time()))
