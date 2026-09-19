"""FC2 Content Market raw HTML crawler."""

from typing import ClassVar
from urllib.parse import urlsplit

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider


class Fc2Spider(BaseSpider):
    version = '0.1.0'
    name = 'fc2'
    allowed_domains: ClassVar = ['adult.contents.fc2.com']
    start_urls: ClassVar = ['https://adult.contents.fc2.com/']
    deep_start_urls = start_urls
    rules = (
        Rule(LinkExtractor(allow=r'/search/|/sub_top\.php', restrict_xpaths='//main|//body'), follow=True),
        Rule(LinkExtractor(allow=r'/article/\d+/?(?:\?.*)?$'), follow=False, callback='handle_item'),
    )
    deep_rules = rules
    custom_settings: ClassVar = {
        'USER_AGENT': 'Mozilla/5.0',
    }

    def handle_item(self, response):
        external_id = urlsplit(response.url).path.rstrip('/').rsplit('/', 1)[-1]
        response.meta['detail_url'] = response.url
        self.logger.info('fc2 detail url=%s external_id=%s', response.url, external_id)
        return super().handle_item(response)
