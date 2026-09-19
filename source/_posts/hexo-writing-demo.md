---
# ===== 基础字段（Hexo 通用）=====
title: 示例：一篇文章的全部写法      # 文章标题
date: 2026-09-19 13:20:00           # 发布时间，不填默认文件创建时间
updated:                            # 更新时间，留空自动用文件修改时间
categories: [编程]                  # 分类：建议每篇只挂 1 个；多级分类写 [编程, C++]
tags: [Hexo, 教程]                  # 标签：可挂多个，用于横向关联文章

# ===== anzhiyu 主题扩展字段 =====
cover:                              # 文章列表封面图 URL，留空用主题默认随机图
top_img:                            # 文章页顶部大图，留空用默认
description: 这是一篇演示 front matter 写法的示例文章，看完就可以删掉。  # SEO/分享描述
comments: true                      # 本文是否开启评论（需先配置评论系统）
# sticky: 1                         # 置顶权重，数字越大越靠前，不需要就删掉这行
# toc: true                         # 是否显示右侧目录，默认开

# 写完正文的「---」下面才是内容。删除本文前，记得 git add/commit/push 才会同步线上。
---

## 这是一级内容标题

正文用标准 Markdown 写。这行上面的 front matter 里，**最常用就四个**：`title`、`date`、`categories`、`tags`。

### 摘要分割线

列表页只显示 `<!-- more -->` 之前的内容作为摘要：

<!-- more -->

### 代码块

```cpp
#include <print>

int main() {
    std::println("Hello, Hexo!");
}
```

### 链接与图片

- 站内链接直接写相对路径：`[归档](/archives/)`
- 图片建议放在 `source/img/` 目录下，引用 `/img/xxx.png`

> 提示：本地 `npx hexo server -p 4000` 可实时预览；`git push` 后约 1~2 分钟线上自动更新。
