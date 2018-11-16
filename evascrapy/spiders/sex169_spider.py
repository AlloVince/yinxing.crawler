# -*- coding: utf-8 -*-
import math
import time
import os
from scrapy.spiders import Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.http import Response, Request
from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class DownloadRequest(Request):
    def __str__(self):
        return "<%s %s meta %s>" % (self.method, self.url, self.meta)


domain = os.environ.get('DOMAIN') or 'b000.top'


class Sex169Spider(BaseSpider):
    version = '1.0.0'
    name = 'sex169'
    allowed_domains = [domain]
    start_urls = [
        'http://%s/forum.php' % domain,
    ]

    deep_start_urls = [
        'http://%s/forum.php' % domain,
    ]

    rules = (
        Rule(LinkExtractor(allow='mod=forumdisplay&fid=(93|160|133|53|45|137|138)$', ), follow=True),
        Rule(LinkExtractor(allow='mod=forumdisplay&fid=(93|160|133|53|45|137|138)&page=(1|2|3|4|5|6|7|8|9)$', ),
             follow=True),
        Rule(LinkExtractor(allow='mod=viewthread&tid=\d+&extra=page%3D\d+$', ), follow=True, callback='handle_page'),
    )

    deep_rules = (
        Rule(LinkExtractor(allow='mod=forumdisplay&fid=(93|160|133|53|45|137|138)$', ), follow=True),
        Rule(LinkExtractor(allow='mod=forumdisplay&fid=(93|160|133|53|45|137|138)&page=\d+$', ), follow=True),
        Rule(LinkExtractor(allow='mod=viewthread&tid=\d+&extra=page%3D\d+$', ), follow=True, callback='handle_page'),
    )

    def handle_page(self, response: Response) -> TorrentFileItem:
        torrents = response.css('a[href^="forum.php?mod=attachment"]:contains("torrent")::attr(href)').extract()
        if len(torrents) < 1:
            return
        for torrent in torrents:
            request = DownloadRequest(
                url=response.urljoin(torrent),  # relative url to absolute
                callback=self.handle_item,
                dont_filter=True
            )
            request.meta['from_url'] = response.url
            yield request

    def handle_item(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta['from_url'],
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
