# 喜多喜多的博客

这是一个使用 Hexo 与 AnZhiYu 主题构建的个人博客。文章采用 `Edit.md + md` 双文件工作流：平时只编辑 `.Edit.md`，Python 工具负责转换图片路径、同步资源并生成 Hexo 使用的 `.md`。

## 环境要求

- Node.js 与 npm/npx
- Python 3.9 或更高版本
- Git

安装 Node.js 依赖：

```powershell
npm install
```

查看工具帮助：

```powershell
python tools/post_workflow.py --help
```

## 1. 新建草稿

```powershell
python tools/post_workflow.py new srp/SRPIntroduction "SRP 入门"
```

生成：

```text
source/_drafts/srp/SRPIntroduction.Edit.md
source/_drafts/srp/SRPIntroduction.md
source/images/posts/srp/SRPIntroduction/
```

只需要使用 Typora 编辑 `SRPIntroduction.Edit.md`，不要直接修改生成的 `SRPIntroduction.md`。

## 2. 插入图片

编辑稿的固定公共资源前缀为：

```text
/images/posts/<文章路径>/
```

例如：

```markdown
![渲染流程](/images/posts/srp/SRPIntroduction/pipeline.png)
```

图片放在：

```text
source/images/posts/srp/SRPIntroduction/pipeline.png
```

新建草稿时会自动写入 Typora 的 `typora-root-url` 和 `typora-copy-images-to`。同步时，工具会将图片路径转换成 Hexo 的相对资源路径，并把图片复制到文章同名资源目录。

封面固定使用：

```text
source/images/posts/srp/SRPIntroduction/cover.png
```

## 3. 同步并预览

```powershell
python tools/post_workflow.py preview
```

该命令会：

1. 同步 `_drafts` 与 `_posts` 中的全部 `.Edit.md`；
2. 执行 `hexo clean`；
3. 在 `http://localhost:4000` 启动预览。

使用其他端口：

```powershell
python tools/post_workflow.py preview --port 5000
```

按 `Ctrl+C` 停止预览。

## 4. 同步并提交 Git

提交说明是必填参数；不提供 `-m/--message` 时命令会直接退出，不会修改 Git 状态。

只提交、不推送：

```powershell
python tools/post_workflow.py commit -m "docs: update SRP article"
```

同步、构建、提交并推送：

```powershell
python tools/post_workflow.py commit -m "docs: update SRP article" --push
```

执行顺序为：同步全部编辑稿、清理 Hexo、完整生成、`git add -A`、`git commit`，以及可选的 `git push`。推送 `main` 后 GitHub Actions 会部署网站。

## 5. 发布草稿

```powershell
python tools/post_workflow.py publish srp/SRPIntroduction
```

工具会先同步，然后把以下内容从 `_drafts` 移动到 `_posts`：

```text
SRPIntroduction.Edit.md
SRPIntroduction.md
SRPIntroduction/
```

公共 Typora 图片目录会继续保留，发布后仍可用 Typora 编辑 `_posts` 中的 `.Edit.md`。

如果目标文章已经存在，并且确认需要覆盖：

```powershell
python tools/post_workflow.py publish srp/SRPIntroduction --force
```

## Front Matter 示例

```yaml
---
title: SRP 入门
date: 2026-09-19 18:00:00
categories:
  - SRP
tags:
  - Unity
  - SRP
  - 渲染
description: Unity SRP 入门笔记
cover: /images/posts/srp/SRPIntroduction/cover.png
---
```

`.Edit.md` 已通过 Hexo 的 `ignore` 配置排除，不会生成重复页面。

## 文档编写规范

### 代码块语言

- 围栏代码块应优先填写准确的语言标记，例如 `csharp`、`hlsl`、`yaml`、`powershell` 或 `markdown`。
- 不要因为不确定语言就统一写成 `plaintext`；应先确认代码实际使用的语言。
- `plaintext` 只用于确实没有语法结构、但仍需要以代码块展示的纯文本，例如终端输出、日志或固定格式的数据。
- 普通说明、单个路径和短命令优先使用正文或内联代码，不要为了排版额外创建 `plaintext` 代码块。
