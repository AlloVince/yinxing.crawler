"""Minnano AV actress profiles."""

from typing import ClassVar

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


class MinnanoAvSpider(BaseSpider):
    version = '1.0.0'
    name = 'minnano_av'
    allowed_domains: ClassVar = ['www.minnano-av.com']
    start_urls: ClassVar = ['https://www.minnano-av.com/actress_list.html']
    deep_start_urls = start_urls
    custom_settings: ClassVar = {'USER_AGENT': 'Mozilla/5.0'}

    rules = (
        Rule(
            LinkExtractor(allow=r'/actress_list(?:\.html|\.php)(?:\?page=[1-9]\d*)?$'),
            follow=True,
        ),
        Rule(
            LinkExtractor(allow=r'/actress\d+\.html(?:\?.*)?$'),
            follow=False,
            callback='handle_item',
        ),
    )
    deep_rules = rules
