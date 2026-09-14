"""Minnano AV actress profiles."""

from typing import ClassVar
from urllib.parse import urlsplit, urlunsplit

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


def canonicalize_actress_url(url: str) -> str:
    """Treat the optional actress name query as display text, not identity."""
    parsed = urlsplit(url)
    if parsed.path.rsplit('/', 1)[-1].startswith('actress') and parsed.path.endswith('.html'):
        return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, '', ''))
    return url


def canonicalize_actress_link(value: str) -> str:
    return canonicalize_actress_url(value)


class MinnanoAvSpider(BaseSpider):
    version = '1.1.0'
    name = 'minnano_av'
    allowed_domains: ClassVar = ['www.minnano-av.com']
    start_urls: ClassVar = ['https://www.minnano-av.com/actress_list.html']
    deep_start_urls = start_urls
    custom_settings: ClassVar = {'USER_AGENT': 'Mozilla/5.0'}

    rules = (
        Rule(
            LinkExtractor(
                allow=r'/actress_list(?:\.html|\.php)(?:\?gojuon=[a-z]+(?:&page=[1-9]\d*)?|\?page=[1-9]\d*)?$',
            ),
            follow=True,
        ),
        Rule(
            LinkExtractor(
                allow=r'/actress\d+\.html(?:\?.*)?$',
                process_value=canonicalize_actress_link,
            ),
            follow=False,
            callback='handle_item',
        ),
    )
    deep_rules = rules

    def handle_item(self, response):
        item = super().handle_item(response)
        item['url'] = canonicalize_actress_url(item['url'])
        return item
