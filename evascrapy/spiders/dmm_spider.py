# -*- coding: utf-8 -*-
import math
import time

from scrapy.http import JsonRequest, Request, Response

from evascrapy.base_spider import BaseSpider
from evascrapy.items import RawJsonItem


class DmmSpider(BaseSpider):
    version = '2.0.0'
    name = 'dmm'
    allowed_domains = ['video.dmm.co.jp', 'api.video.dmm.co.jp']
    start_urls = ['https://video.dmm.co.jp/av/list/']
    deep_start_urls = start_urls
    rules = ()
    deep_rules = rules

    search_api_url = 'https://api.video.dmm.co.jp/graphql'
    search_page_size = 120
    search_query = '''
        query AvContentIds($limit: Int!, $offset: Int!) {
          legacySearchPPV(
            limit: $limit
            offset: $offset
            floor: AV
            sort: SALES_RANK_SCORE
            facetLimit: 1
            includeExplicit: true
            excludeUndelivered: true
          ) {
            result {
              contents { id }
              pageInfo { totalCount }
            }
          }
        }
    '''
    detail_query = '''
        query ContentWithReviews($id: ID!, $sort: ReviewSort!) {
          ppvContent(id: $id) {
            id
            title
            description
            contentType
            releaseStatus
            isExclusiveDelivery
            wishlistCount
            duration
            saleStartDate
            saleEndDate
            deliveryStartDate
            packageImage {
              mediumUrl
              largeUrl
              smallUrl
            }
            sampleImages { imageUrl }
            pricing {
              lowestRegularPriceInclusiveTax
              lowestEffectivePriceInclusiveTax
              hasMultiplePrices
            }
            actresses { id name imageUrl }
            genres { id name }
            maker { id name }
            series { id name }
            label { id name }
            directors { id name }
            relatedTags(limit: 100) {
              __typename
              ... on ContentTag { id name }
            }
          }
          reviews(contentId: $id, sort: $sort, limit: 10, offset: 0) {
            items {
              id
              title
              rating
              reviewerId
              nickname
              isPurchased
              comment
              helpfulCount
              service
              isExposure
              publishDate
              __typename
            }
          }
        }
    '''
    review_sort = 'HELPFUL_COUNT_DESC'

    async def start(self):
        for url in self.start_urls:
            yield Request(url, cookies={'age_check_done': '1'})

    def parse_start_url(self, response: Response):
        yield self._build_search_request(offset=0)

    def _build_search_request(self, offset: int) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'query': self.search_query,
                'variables': {'limit': self.search_page_size, 'offset': offset},
            },
            callback=self.parse_search_results,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': self.start_urls[0],
            },
            meta={'offset': offset},
        )

    def parse_search_results(self, response: Response):
        result = response.json()['data']['legacySearchPPV']['result']
        contents = result['contents']

        for content in contents:
            yield self._build_detail_request(content['id'])

        next_offset = response.meta['offset'] + len(contents)
        if contents and next_offset < result['pageInfo']['totalCount']:
            yield self._build_search_request(offset=next_offset)

    def _build_detail_request(self, content_id: str) -> JsonRequest:
        return JsonRequest(
            url=self.search_api_url,
            data={
                'operationName': 'ContentWithReviews',
                'query': self.detail_query,
                'variables': {'id': content_id, 'sort': self.review_sort},
            },
            callback=self.parse_detail,
            cookies={'age_check_done': '1'},
            headers={
                'Origin': 'https://video.dmm.co.jp',
                'Referer': self.start_urls[0],
            },
            meta={
                'content_id': content_id,
                'detail_url': f'https://video.dmm.co.jp/av/content/?id={content_id}',
            },
        )

    def parse_detail(self, response: Response) -> RawJsonItem:
        payload = response.json()
        if payload.get('errors'):
            raise RuntimeError('DMM detail GraphQL errors: %s' % payload['errors'])

        data = payload.get('data') or {}
        if not data.get('ppvContent'):
            raise RuntimeError('DMM detail GraphQL returned no content: %s' % response.meta['content_id'])

        return RawJsonItem(
            url=response.meta['detail_url'],
            version=self.version,
            task=self.settings.get('APP_TASK'),
            timestamp=math.floor(time.time()),
            content=payload,
        )
