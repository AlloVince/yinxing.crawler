# -*- coding: utf-8 -*-
import os
import math
import time
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Response, Request
from evascrapy.items import TorrentFileItem

domain = os.environ.get('DOMAIN') or 'onejav.com'


class OnejavSpider(BaseSpider):
    version = '1.0.0'
    name = 'onejav'
    allowed_domains = [domain]
    start_urls = [
        'https://%s/new' % domain,
    ]

    deep_start_urls = [
        'https://%s/actress/' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='/new\?page=(1|2|3|4|5|6|7|8|9|10|11|12|13|14|15)$', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/.+\.torrent$', ), follow=True, callback='handle_torrent'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/actress/\?page=\d+', ), follow=True),
        Rule(LinkExtractor(allow='/actress/[^/]+', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/.+\.torrent$', ), follow=True, callback='handle_torrent'),
    )
