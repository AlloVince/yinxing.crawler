# yinxing.crawler

Spiders based on [EvaScrapy](https://github.com/AlloVince/EvaScrapy). The image
contains the complete set of spiders synchronized from EvaScrapy's local
development copies.

## nyaa 运行约定

`crawler.18x.yml` 当前只部署 `crawler-nyaa`。nyaa 的详情页会产生 torrent 下载请求，
请求必须把最终下载 URL 放入 `request.meta['detail_url']`，以便 EvaScrapy 的
`S3DupeFilter` 使用 URL marker 做跨运行防重。torrent 内容本身仍按 bencode 的
`info` 字典计算 SHA-1，并以 info_hash 分片路径保存。

发布与验收注意事项：

- yinxing.crawler 镜像依赖 EvaScrapy 的已发布版本；先发布 EvaScrapy，再更新 Dockerfile 的 `FROM` 并发布 yinxing.crawler。
- 必须在目标镜像中实际 import 运行时依赖，并检查镜像 tag 的 digest/创建时间；CI 通过不等于 NAS 已拉到新镜像。
- 不要在 NAS 上使用多个 `docker-compose run` 实例模拟常驻服务；nyaa 默认只能有一个实例，避免被目标站点封禁 IP。

## FANZA

- 入口：`https://video.dmm.co.jp/av/list/`
- 详情：`https://video.dmm.co.jp/av/content/?id={content_id}`
- 入口需要年龄确认 Cookie：`age_check_done=1`
- 搜索页是 Next.js 客户端渲染页面，原始 HTML 没有详情链接；列表数据来自 `https://api.video.dmm.co.jp/graphql`
- `legacySearchPPV` 可按 `offset` 分页读取内容 ID；当前使用 `floor: AV`、`sort: SALES_RANK_SCORE`
- Spider 先遍历演员目录，再按演员筛选分页请求列表 API；详情请求通过 GraphQL 合并影片信息和第一页评论，原始响应以 JSON 落盘
- 默认普通抓取使用 `sort: DATE`，只抓列表前 10 页；设置 `APP_RUN_DEEP=1` 时执行演员目录 → 演员列表 → 详情的深度抓取
- 详情 URL 不能删除 query；`id` 是定位内容的必需参数
- GraphQL 查询和字段说明见 [`docs/dmm-graphql.md`](docs/dmm-graphql.md)
- 列表搜索参数、筛选字段和分片策略见 [`docs/dmm-search-parameters.md`](docs/dmm-search-parameters.md)
- 演员目录接口、五十音参数和演员分页规则见 [`docs/dmm-actress-directory.md`](docs/dmm-actress-directory.md)

## DMM DVD

The `dmm` spider uses maker catalogues first and actress catalogues as a supplement,
with canonical detail deduplication and isolated durable queues. See
[`docs/dmm-catalog-crawl.md`](docs/dmm-catalog-crawl.md) for boundaries, recovery and validation.
