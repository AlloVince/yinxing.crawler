# -*- coding: utf-8 -*-
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider

domain = os.environ.get('DOMAIN') or 'myporn.club'


class MypornSpider(BaseSpider):
    version = '1.0.0'
    name = 'myporn'
    allowed_domains = [domain, 'ct1.myporn.club']
    start_urls = [
        'http://%s/torrents' % domain,
    ]

    deep_start_urls = [
        'http://%s/torrents' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='/torrents/(1|2|3|4|5|6|7|8|9|10)$', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/\w+$', ), follow=True),
        Rule(LinkExtractor(allow='/download\.php.+', ), follow=False, callback='handle_torrent'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/torrents/\d+$', ), follow=True),
        Rule(LinkExtractor(allow='/torrent/\w+$', ), follow=True),
        Rule(LinkExtractor(allow='/download\.php.+', ), follow=False, callback='handle_torrent'),
    )
