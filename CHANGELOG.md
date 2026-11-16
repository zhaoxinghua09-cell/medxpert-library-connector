# Changelog

## 1.0.2 — 2026-11-17

**Registry icon pinned to a release tag instead of a branch.**

The `icons` entry in `server.json` pointed at `@main`. A registry entry is a
published fact, but `@main` is a moving target: the picture behind a version's
metadata could change, or 404, without any new version being published — and
nobody would notice, because the registry keeps serving whatever it captured
at publish time while clients dereference the URL live.

The icon now points at `@v1.0.2`, the tag that carries this release. Same
picture, now immutable.

No functional change: the server, its four tools and the bundled sample wiki
are byte-identical to 1.0.1.

---

## 1.0.2 — 2026-11-17（中文）

**Registry 图标从分支改为钉在版本标签上。**

`server.json` 的 `icons` 指向 `@main`。但 Registry 条目是"已发布的事实"，而
`@main` 是移动目标：某个版本的元数据背后那张图可以不发新版本就被换掉、或者
404，而且不会有人察觉——Registry 保留发布时抓取的内容，客户端却是实时取这个
URL。

现在指向 `@v1.0.2`，即本次发布所在的标签。图没变，但它不再会变。

功能无改动：服务、四个工具、自带示例 wiki 与 1.0.1 完全一致。
