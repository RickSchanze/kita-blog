---
title: Hexo 从草稿到发布：我的写作工作流
date: 2026-09-19 14:00:00
updated: 2026-09-19 14:00:00
categories:
  - 编程
tags:
  - Hexo
  - 教程
description: 一套简单可靠的 Hexo 写作、预览、发布和部署流程。
cover: /imgs/QQ头像.jpg
mathjax: true
---

Hexo 的核心很简单：Markdown 是内容，主题负责展示，生成器把两者组合成静态网页。把流程固定下来以后，写作就不必反复处理部署细节。

## 创建草稿

```bash
npx hexo new draft "文章标题"
```

草稿保存在 `source/_drafts`，普通构建不会把它发布出去。需要预览草稿时运行：

```bash
npx hexo server --draft
```

## 编写 Front Matter

每篇文章开头的 YAML 区域负责描述文章。分类更像目录，适合少而稳定；标签更像关键词，可以灵活组合。

## 发布与检查

```bash
npx hexo publish "文章标题"
npx hexo clean
npx hexo generate
npx hexo server
```

提交代码前，我会至少检查首页、文章页、移动端菜单和一张本地图片。静态站点的优点是部署结果可重复：同一份源码和依赖锁文件，应当得到相同的输出。

## 一个公式示例

$$
T(n) = T(n-1) + O(1) = O(n)
$$

内容完成后推送到 `main` 分支，GitHub Actions 会自动构建并同步到服务器。
