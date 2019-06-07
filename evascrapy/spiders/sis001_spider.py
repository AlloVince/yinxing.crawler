# -*- coding: utf-8 -*-
import math
import time
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, Request
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


domain = os.environ.get('DOMAIN') or 'sis001.com'


class SisSpider(BaseSpider):
    version = '1.0.0'
    name = 'sis001'
    allowed_domains = [domain]
    start_urls = [
        'http://%s/forum/index.php' % domain,
    ]

    deep_start_urls = [
        'http://%s/forum/index.php' % domain,
    ]

    rules = (
        Rule(
            LinkExtractor(allow='forum-(143|230|229|231|25|58|77|27)-(1|2|3|4|5)\.html', ),
            follow=True
        ),
        Rule(LinkExtractor(allow='thread-\d+-1-\d+.html', ), follow=True),
        Rule(LinkExtractor(allow='attachment\.php\?aid=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='attachment\.php\?aid=\d+&clickDownload=1$', ), follow=False,
             callback='handle_torrent'),
    )

    deep_rules = (
        Rule(
            LinkExtractor(allow='forum-(143|230|229|231|25|58|77|27)-\d+\.html', ),
            follow=True
        ),
        Rule(LinkExtractor(allow='thread-\d+-1-\d+.html', ), follow=True),
        Rule(LinkExtractor(allow='attachment\.php\?aid=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='attachment\.php\?aid=\d+&clickDownload=1$', ), follow=False,
             callback='handle_torrent'),
    )
