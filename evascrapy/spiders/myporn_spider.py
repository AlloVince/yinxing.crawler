# -*- coding: utf-8 -*-
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider

domain = os.environ.get('DOMAIN') or 'myporn.club'


class MypornSpider(BaseSpider):
    version = '1.1.0'
    name = 'myporn'
    allowed_domains = [domain, 'ct1.myporn.club']
    start_urls = ['https://%s/ts' % domain]
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'/ts(?:/\d+)?$'), follow=True),
        Rule(LinkExtractor(allow=r'/t/[A-Za-z0-9]+$'), follow=True),
        Rule(LinkExtractor(allow=r'/download\.php\?.+'), follow=False, callback='handle_torrent'),
    )
    deep_rules = rules
