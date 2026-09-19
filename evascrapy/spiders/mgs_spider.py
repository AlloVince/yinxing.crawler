"""MGS video raw HTML crawler."""

from typing import ClassVar

from scrapy import Request

from evascrapy.base_spider import BaseSpider


class MgsSpider(BaseSpider):
    version = '0.1.0'
    name = 'mgs'
    allowed_domains: ClassVar = ['www.mgstage.com']
    start_urls: ClassVar = [
        'https://www.mgstage.com/',
        'https://www.mgstage.com/search/cSearch.php?sort=popular&list_cnt=120&range=campaign&type=top',
    ]
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules
    custom_settings: ClassVar = {
        'USER_AGENT': 'Mozilla/5.0',
        'COOKIES_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {'Cookie': 'adc=1; coc=1'},
    }

    def handle_item(self, response):
        response.meta['detail_url'] = response.url
        self.logger.info('mgs detail url=%s external_id=%s', response.url, response.url.rstrip('/').rsplit('/', 1)[-1])
        return super().handle_item(response)

    def parse_start_url(self, response):
        for href in response.css('a[href*="/product/product_detail/"]::attr(href)').getall()[:20]:
            yield response.follow(href, callback=self.handle_item)

    def start_requests(self):
        for url in self.start_urls:
            yield Request(url, headers={'Cookie': 'adc=1; coc=1'}, callback=self.parse_listing)

    def parse_listing(self, response):
        self.logger.info('mgs listing url=%s', response.url)
        for href in response.css('a[href*="/product/product_detail/"]::attr(href)').getall()[:20]:
            yield response.follow(href, callback=self.handle_item, headers={'Cookie': 'adc=1; coc=1'})
