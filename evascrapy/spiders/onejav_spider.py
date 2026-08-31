# -*- coding: utf-8 -*-
import os

from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor

from evascrapy.base_spider import BaseSpider


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
        Rule(LinkExtractor(allow=r'/new(?:\?page=\d+)?$'), follow=True),
        Rule(LinkExtractor(allow=r'/torrent/.+\.torrent$'), follow=False, callback='handle_torrent'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow=r'/actress/(?:\?page=\d+)?$'), follow=True),
        Rule(LinkExtractor(allow=r'/actress/[^/]+$'), follow=True),
        Rule(LinkExtractor(allow=r'/torrent/.+\.torrent$'), follow=False, callback='handle_torrent'),
    )
    custom_settings = {
        # OneJAV intermittently returns 503 at the catalogue entry point.
        'RETRY_TIMES': 5,
    }
