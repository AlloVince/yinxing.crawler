# yinxing.crawler

Spiders based on [EvaScrapy](https://github.com/AlloVince/EvaScrapy)

## DMM

- 入口：`https://video.dmm.co.jp/av/list/`
- 详情：`https://video.dmm.co.jp/av/content/?id={content_id}`
- 入口需要年龄确认 Cookie：`age_check_done=1`
- 搜索页是 Next.js 客户端渲染页面，原始 HTML 没有详情链接；列表数据来自 `https://api.video.dmm.co.jp/graphql`
- `legacySearchPPV` 可按 `offset` 分页读取内容 ID；当前使用 `floor: AV`、`sort: SALES_RANK_SCORE`
- Spider 先访问搜索页，再请求列表 API；详情请求通过 GraphQL 合并影片信息和第一页评论，原始响应以 JSON 落盘
- 详情 URL 不能删除 query；`id` 是定位内容的必需参数
- GraphQL 查询和字段说明见 [`docs/dmm-graphql.md`](docs/dmm-graphql.md)
