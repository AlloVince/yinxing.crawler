# -*- coding: utf-8 -*-
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from evascrapy.base_spider import BaseSpider
from scrapy.http import Request


class DmmSpider(BaseSpider):
    version = '1.0.0'
    name = 'dmm'
    allowed_domains = ['www.dmm.co.jp']
    start_urls = [
        'https://www.dmm.co.jp/digital/videoa/-/list/=/sort=date/'
    ]

    deep_start_urls = [
        'https://www.dmm.co.jp/digital/videoa/-/list/=/sort=date/',
        'https://www.dmm.co.jp/digital/videoa/-/genre/=/display=syllabary/sort=ranking/',
        'https://www.dmm.co.jp/digital/videoa/-/maker/',
        'https://www.dmm.co.jp/digital/videoa/-/series/=/keyword=a/sort=ruby/',
        'https://www.dmm.co.jp/digital/videoa/-/actress/=/keyword=a/',
    ]

    rules = (
        Rule(LinkExtractor(allow='digital/videoa/-/list/=/sort=date/page=([1-9]|10)/', ), follow=True),
        Rule(LinkExtractor(allow='digital/\w+/-/detail/=/cid=(\w+)/(.*)$', ), follow=False,
             callback='handle_item'),
    )

    deep_rules = (
        # Enter pages
        Rule(LinkExtractor(allow='digital/\w+/-/actress/=/keyword=\w+/(page=\d+/)*$', ), follow=True, ),
        Rule(LinkExtractor(allow='digital/\w+/-/maker/=/keyword=\w+/(page=\d+/)*$', ), follow=True, ),
        Rule(LinkExtractor(allow='digital/\w+/-/series/=/keyword=\w+/sort=ruby/(page=\d+/)*$', ), follow=True, ),
        # List pages
        Rule(LinkExtractor(
            allow='digital/videoa/-/list/=/article=(actress|series|maker|keyword)/id=\d+/(page=\d+/)*$', ),
            follow=True, ),
        Rule(LinkExtractor(allow='digital/\w+/-/detail/=/cid=(\w+)/(.*)$', ),
             follow=True,
             callback='handle_item'),
    )

    def _build_request(self, rule, link):
        # ignore url query for dmm spider
        r = Request(url=link.url.split('?')[0], callback=self._response_downloaded)
        r.meta.update(rule=rule, link_text=link.text)
        return r
