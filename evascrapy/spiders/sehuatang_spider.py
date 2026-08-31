# -*- coding: utf-8 -*-
"""Public-only SeHuaTang Discuz pages and openly exposed torrent attachments."""
import math
import time

from scrapy.http import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import Rule

from evascrapy.base_spider import BaseSpider
from evascrapy.items import TorrentFileItem


class SehuatangSpider(BaseSpider):
    name = 'sehuatang'
    version = '1.0.0'
    allowed_domains = ['www.sehuatang.net']
    start_urls = ['https://www.sehuatang.net/forum.php']
    deep_start_urls = start_urls

    # The rules deliberately begin at the public forum index.  No login,
    # cookie, invite-code, challenge-solving, or guessed private board URL is
    # used.  Attachment links are followed only when a public thread exposes
    # them in its HTML.
    rules = (
        Rule(LinkExtractor(
            allow=r'/(?:forum\.php\?mod=forumdisplay&fid=\d+[^#]*|forum-\d+-\d+\.html)$'
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'/(?:forum\.php\?mod=viewthread&tid=\d+[^#]*|thread-\d+-\d+-\d+\.html)$'
        ), follow=True),
        Rule(LinkExtractor(
            allow=r'/forum\.php\?mod=attachment&[^#]*'
        ), follow=False, callback='handle_attachment'),
    )
    deep_rules = rules
    custom_settings = {'CLOSESPIDER_ITEMCOUNT': 0}

    def handle_attachment(self, response: Response):
        # A login/challenge response is HTML even when the original link was
        # named *.torrent.  Discuz torrent files are bencoded dictionaries;
        # this cheap check prevents those pages becoming false items.
        body = response.body.lstrip()
        content_type = response.headers.get('Content-Type', b'').lower()
        disposition = response.headers.get('Content-Disposition', b'').lower()
        looks_like_torrent = (
            body.startswith(b'd') and b'4:info' in body[:4096]
            and (b'torrent' in content_type or b'torrent' in disposition
                 or 'torrent' in response.url.lower())
        )
        if not looks_like_torrent:
            self.logger.info('Skipping non-public/non-torrent attachment: %s', response.url)
            return None

        return TorrentFileItem(
            url=response.url,
            from_url=response.request.headers.get('Referer', b'').decode(
                'utf-8', errors='replace'
            ),
            task=self.settings.get('APP_TASK'),
            version=self.version,
            timestamp=math.floor(time.time()),
            body=response.body,
        )
