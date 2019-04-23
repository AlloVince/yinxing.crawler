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
domain2 = os.environ.get('DOMAIN2') or 'www.javbus.work'

regex = re.compile(
    r"<script>[\n\s]+var gid = (\d+);[\n\s]+var uc = (\d+);[\n\s]+var img = '(http[\w:\/\.]+)';[\n\s]*</script>", re.S)

magnet = re.compile(r"magnet:\?xt=urn:btih:[a-zA-Z0-9]{40,40}")


class JavbusSpider(BaseSpider):
    version = '1.0.0'
    name = 'javbus'
    allowed_domains = [domain, domain2]
    start_urls = [
        'https://%s' % domain,
        'https://%s' % domain2,
    ]

    deep_start_urls = [
        'https://%s' % domain,
        'https://%s/actresses' % domain,
        'https://%s/uncensored/actresses' % domain,
        'https://%s/genre' % domain,
        'https://%s' % domain2,
    ]

    rules = (
        Rule(LinkExtractor(allow='/page/(1|2|3|4|5|6|7|8|9)', ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored/page/(1|2|3|4|5|6|7|8|9)' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/[^\/]{3,}$' % domain, ), follow=False, callback='handle_page'),
        Rule(LinkExtractor(allow='%s/[^\/]{3,}$' % domain2, ), follow=False, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='/page/\d+', ), follow=True),
        Rule(LinkExtractor(allow='%s/star/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/genre/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/director/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/studio/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/label/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored/star/\w+/\d+' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored/genre/\w+(/\d+)?' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/uncensored/page/\d+' % domain, ), follow=True),
        Rule(LinkExtractor(allow='%s/[^\/]{3,}$' % domain, ), follow=True, callback='handle_page'),
        Rule(LinkExtractor(allow='%s/[^\/]{3,}$' % domain2, ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> Request:
        match = regex.search(response.text)
        if not match:
            return

        current_domain = response.url.split('//')[-1].split('/')[0]
        request = Request(
            url='https://%s/ajax/uncledatoolsbyajax.php?gid=%s&uc=%s&img=%s' % (
                current_domain, match.group(1), match.group(2), match.group(3)
            ),
            callback=self.handle_ajax,
        )
        request.meta['from_url'] = response.url
        yield request

    def handle_ajax(self, response: Response):
        if not magnet.search(response.text):
            return
        return RawHtmlItem(url=response.meta['from_url'], html=response.text, task=self.settings.get('APP_TASK'),
                           version=self.version, timestamp=math.floor(time.time()))
