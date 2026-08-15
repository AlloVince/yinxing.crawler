# yinxing.crawler

Spiders based on [EvaScrapy](https://github.com/AlloVince/EvaScrapy)

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
