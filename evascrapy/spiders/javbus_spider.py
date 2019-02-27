# -*- coding: utf-8 -*-
import math
import time
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, Request
from evascrapy.base_spider import BaseSpider
from evascrapy.items import RawHtmlItem
import re

domain = os.environ.get('DOMAIN') or 'www.javbus.in'

regex = re.compile(
    r"<script>[\n\s]+var gid = (\d+);[\n\s]+var uc = (\d+);[\n\s]+var img = '(http[\w:\/\.]+)';[\n\s]*</script>", re.S)


class JavbusSpider(BaseSpider):
    version = '1.0.0'
    name = 'javbus'
    allowed_domains = [domain]
    start_urls = [
        'https://%s' % domain,
    ]

    deep_start_urls = [
        'https://%s' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='/page/\d+', ), follow=True),
        Rule(LinkExtractor(allow='/[a-zA-Z]+-\d+', ), follow=True, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/page/\d+', ), follow=True),
        Rule(LinkExtractor(allow='/[a-zA-Z]+-\d+', ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> Request:
        match = regex.search(response.text)
        if not match:
            pass

        request = Request(
            url='https://%s/ajax/uncledatoolsbyajax.php?gid=%s&uc=%s&img=%s' % (
                domain, match.group(1), match.group(2), match.group(3)
            ),
            callback=self.handle_ajax,
        )
        request.meta['from_url'] = response.url
        yield request

    def handle_ajax(self, response: Response):
        return RawHtmlItem(url=response.meta['from_url'], html=response.text, task=self.settings.get('APP_TASK'),
                           version=self.version, timestamp=math.floor(time.time()))
