#!/usr/bin/env python3
"""Create and synchronize Typora-friendly Hexo posts.

Editor files use a fixed public asset prefix:
  /images/posts/<post-path>/<filename>

Generated Hexo files use post asset paths:
  <filename>
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source"


def python_hint() -> str:
    return "python tools/post_workflow.py"


def all_editors() -> list[Path]:
    editors = sorted((SOURCE / "_drafts").rglob("*.Edit.md"))
    editors += sorted((SOURCE / "_posts").rglob("*.Edit.md"))
    return editors


def sync_all() -> list[Path]:
    editors = all_editors()
    if not editors:
        print("没有找到 *.Edit.md")
        return []
    changed: list[Path] = []
    for editor in editors:
        changed.extend(sync_one(editor, git_add=False))
    return changed


def run_hexo(*arguments: str) -> None:
    executable = "npx.cmd" if os.name == "nt" else "npx"
    subprocess.run([executable, "hexo", *arguments], cwd=ROOT, check=True)


def safe_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value.replace("\\", "/").strip("/"))
    if not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("文章路径不能为空，也不能包含 . 或 ..")
    return path.with_suffix("")


def paths_for(layout: str, post_path: PurePosixPath) -> tuple[Path, Path, Path, str]:
    content_root = SOURCE / ("_drafts" if layout == "draft" else "_posts")
    base = content_root.joinpath(*post_path.parts)
    editor = base.with_name(base.name + ".Edit.md")
    generated = base.with_suffix(".md")
    public_prefix = "/images/posts/" + post_path.as_posix() + "/"
    public_assets = SOURCE.joinpath("images", "posts", *post_path.parts)
    return editor, generated, public_assets, public_prefix


def new_post(args: argparse.Namespace) -> None:
    post_path = safe_path(args.path)
    editor, generated, public_assets, public_prefix = paths_for(args.layout, post_path)
    if editor.exists() and not args.force:
        raise FileExistsError(f"已存在：{editor}")

    editor.parent.mkdir(parents=True, exist_ok=True)
    public_assets.mkdir(parents=True, exist_ok=True)
    typora_root = os.path.relpath(SOURCE, editor.parent).replace("\\", "/")
    typora_copy = os.path.relpath(public_assets, editor.parent).replace("\\", "/")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text = f'''---
title: {args.title}
date: {now}
categories:
tags:
description:
cover: {public_prefix}cover.png
typora-root-url: {typora_root}
typora-copy-images-to: {typora_copy}
---

# {args.title}

正文从这里开始。

<!-- Typora 中插图统一使用：![说明]({public_prefix}图片名.png) -->
'''
    editor.write_text(text, encoding="utf-8", newline="\n")
    sync_one(editor, git_add=False)
    print(f"已创建编辑稿：{editor.relative_to(ROOT)}")
    print(f"已创建 Hexo 稿：{generated.relative_to(ROOT)}")
    print(f"公共资源目录：{public_assets.relative_to(ROOT)}")


def locate_editor(editor_arg: str) -> Path:
    candidate = Path(editor_arg)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    if ROOT not in candidate.parents or not candidate.name.endswith(".Edit.md"):
        raise ValueError("必须指定项目内的 *.Edit.md 文件")
    if not candidate.exists():
        raise FileNotFoundError(candidate)
    return candidate


def editor_metadata(editor: Path) -> tuple[Path, Path, str]:
    try:
        relative = editor.relative_to(SOURCE / "_drafts")
    except ValueError:
        relative = editor.relative_to(SOURCE / "_posts")
    plain_name = editor.name.removesuffix(".Edit.md")
    relative_post = relative.parent / plain_name
    generated = editor.with_name(plain_name + ".md")
    public_assets = SOURCE / "images" / "posts" / relative_post
    prefix = "/images/posts/" + relative_post.as_posix() + "/"
    return generated, public_assets, prefix


def sync_one(editor: Path, git_add: bool) -> list[Path]:
    generated, public_assets, prefix = editor_metadata(editor)
    text = editor.read_text(encoding="utf-8")
    # Convert the fixed Typora/public prefix to Hexo post-asset-relative paths.
    text = text.replace(prefix, "")
    # Typora-only keys must not leak into the published article.
    text = re.sub(r"(?m)^typora-(?:root-url|copy-images-to):.*\n?", "", text)
    generated.write_text(text, encoding="utf-8", newline="\n")

    article_assets = generated.with_suffix("")
    article_assets.mkdir(parents=True, exist_ok=True)
    if public_assets.exists():
        shutil.copytree(public_assets, article_assets, dirs_exist_ok=True)

    changed = [editor, generated, public_assets, article_assets]
    if git_add:
        existing = [str(path.relative_to(ROOT)) for path in changed if path.exists()]
        subprocess.run(["git", "add", "--", *existing], cwd=ROOT, check=True)
    print(f"已同步：{editor.relative_to(ROOT)} -> {generated.relative_to(ROOT)}")
    return changed


def preview_site(args: argparse.Namespace) -> None:
    sync_all()
    run_hexo("clean")
    print(f"预览地址：http://localhost:{args.port}")
    print("按 Ctrl+C 停止服务器。")
    run_hexo("server", "--port", str(args.port))


def commit_site(args: argparse.Namespace) -> None:
    sync_all()
    run_hexo("clean")
    run_hexo("generate")
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True)
    unchanged = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT).returncode == 0
    if unchanged:
        print("没有需要提交的改动。")
        return
    subprocess.run(["git", "commit", "-m", args.message], cwd=ROOT, check=True)
    if args.push:
        subprocess.run(["git", "push"], cwd=ROOT, check=True)
    else:
        print("提交完成。需要部署时执行 git push，或下次使用 commit --push。")


def publish_post(args: argparse.Namespace) -> None:
    editor_arg = args.editor
    if not editor_arg.endswith(".Edit.md"):
        editor_arg = str(SOURCE / "_drafts" / (safe_path(editor_arg).as_posix() + ".Edit.md"))
    editor = locate_editor(editor_arg)
    drafts_root = SOURCE / "_drafts"
    try:
        relative_editor = editor.relative_to(drafts_root)
    except ValueError as exc:
        raise ValueError("只能发布 source/_drafts 中的编辑稿") from exc

    generated, public_assets, _ = editor_metadata(editor)
    sync_one(editor, git_add=False)
    article_assets = generated.with_suffix("")
    target_editor = SOURCE / "_posts" / relative_editor
    plain_name = editor.name.removesuffix(".Edit.md")
    target_generated = target_editor.with_name(plain_name + ".md")
    target_assets = target_generated.with_suffix("")

    for target in (target_editor, target_generated, target_assets):
        if target.exists() and not args.force:
            raise FileExistsError(f"发布目标已存在：{target.relative_to(ROOT)}")

    target_editor.parent.mkdir(parents=True, exist_ok=True)
    if args.force:
        for target in (target_editor, target_generated):
            if target.exists():
                target.unlink()
        if target_assets.exists():
            shutil.rmtree(target_assets)

    shutil.move(str(editor), str(target_editor))
    shutil.move(str(generated), str(target_generated))
    if article_assets.exists():
        shutil.move(str(article_assets), str(target_assets))

    print(f"已发布编辑稿：{target_editor.relative_to(ROOT)}")
    print(f"已发布 Hexo 稿：{target_generated.relative_to(ROOT)}")
    if public_assets.exists():
        print(f"公共资源保留在：{public_assets.relative_to(ROOT)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Typora + Hexo 双文件文章工作流",
        epilog=(
            "常用示例：\n"
            f"  {python_hint()} new srp/SRPIntroduction \"SRP 入门\"\n"
            f"  {python_hint()} preview\n"
            f"  {python_hint()} commit -m \"docs: update SRP article\" --push\n"
            f"  {python_hint()} publish srp/SRPIntroduction"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    commands = parser.add_subparsers(dest="command", required=True)

    new_cmd = commands.add_parser("new", help="创建 Edit.md 和 Hexo md")
    new_cmd.add_argument("path", help="文章路径，例如 srp/SRPIntroduction")
    new_cmd.add_argument("title", help="文章标题")
    new_cmd.add_argument("--layout", choices=("draft", "post"), default="draft")
    new_cmd.add_argument("--force", action="store_true")
    new_cmd.set_defaults(func=new_post)

    preview_cmd = commands.add_parser("preview", help="同步全部编辑稿并启动本地预览")
    preview_cmd.add_argument("--port", type=int, default=4000, help="预览端口，默认 4000")
    preview_cmd.set_defaults(func=preview_site)

    commit_cmd = commands.add_parser("commit", help="同步、构建检查并提交 Git")
    commit_cmd.add_argument("-m", "--message", required=True, help="Git 提交说明（必填）")
    commit_cmd.add_argument("--push", action="store_true", help="提交成功后执行 git push")
    commit_cmd.set_defaults(func=commit_site)

    publish_cmd = commands.add_parser("publish", help="同步并发布一个草稿")
    publish_cmd.add_argument("editor", help="草稿路径，如 srp/SRPIntroduction，或 Edit.md 路径")
    publish_cmd.add_argument("--force", action="store_true", help="覆盖 _posts 中的同名文章")
    publish_cmd.set_defaults(func=publish_post)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n操作已停止。")
    except (ValueError, FileNotFoundError, FileExistsError, subprocess.CalledProcessError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
