# -*- coding: utf-8 -*-
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider

domain = os.environ.get('DOMAIN') or 'pornleech.is'


class PornleechSpider(BaseSpider):
    version = '1.0.0'
    name = 'pornleech'
    allowed_domains = [domain]
    start_urls = [
        'http://%s/index.php?page=torrents' % domain,
    ]

    deep_start_urls = [
        'http://%s/index.php?page=torrents' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='^/index\.php.+pages=(1|2|3|4|5|6|7|8|9|10)$', ), follow=True),
        Rule(LinkExtractor(allow='.+-\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='download\.php.+\.torrent$', ), follow=False, callback='handle_torrent'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='^/index\.php.+pages=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='.+-\d+\.html$', ), follow=True),
        Rule(LinkExtractor(allow='download\.php.+\.torrent$', ), follow=False, callback='handle_torrent'),
    )

