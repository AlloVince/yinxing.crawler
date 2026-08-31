# -*- coding: utf-8 -*-
"""Academic Torrents' public RSS catalogue."""
import math
import re
import time

from scrapy import Request
from scrapy.http import Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class AcademicTorrentsSpider(BaseSpider):
    version = '1.0.0'
    name = 'academic_torrents'
    allowed_domains = ['academictorrents.com']
    start_urls = ['https://academictorrents.com/rss.xml']
    deep_start_urls = ['https://academictorrents.com/database.xml']
    custom_settings = {'CLOSESPIDER_ITEMCOUNT': 0}

    def parse_start_url(self, response: Response):
        yield from self.parse_catalog(response)

    def parse_catalog(self, response: Response):
        hashes = response.xpath(
            '//*[local-name()="infoHash"]/text()'
        ).getall()
        for info_hash in hashes:
            info_hash = info_hash.strip().lower()
            if re.fullmatch(r'[0-9a-f]{40}', info_hash):
                url = f'https://academictorrents.com/download/{info_hash}.torrent'
                yield Request(
                    url,
                    callback=self.handle_torrent,
                    meta={'from_url': response.url},
                )

    def handle_torrent(self, response: Response) -> TorrentFileItem:
        return TorrentFileItem(
            url=response.url,
            from_url=response.meta.get('from_url', response.url),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
