#!/usr/bin/env python3
"""
使用 Hugging Face Hub 下载模型或分词器资源。

示例:
    python download_model.py --repo qwen/Qwen2.5-1.5B-Instruct --output ../models/qwen2.5-1.5b
"""

from __future__ import annotations

import argparse
import pathlib

from huggingface_hub import snapshot_download


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download model repository from Hugging Face.")
    parser.add_argument(
        "--repo",
        required=True,
        help="仓库名称，例如 qwen/Qwen2.5-1.5B-Instruct。",
    )
    parser.add_argument(
        "--output",
        default=".",
        help="输出目录。默认当前目录。",
    )
    parser.add_argument(
        "--branch",
        default=None,
        help="可选：指定分支/tag，例如 main、int4。",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=None,
        help="可选：仅下载指定通配符文件，例如 'config.json' 'pytorch_model*.bin'。",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=None,
        help="可选：排除文件。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    target_dir = pathlib.Path(args.output).expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    snapshot_download(
        repo_id=args.repo,
        revision=args.branch,
        local_dir=target_dir,
        allow_patterns=args.include,
        ignore_patterns=args.exclude,
    )
    print(f"模型已下载到: {target_dir}")


if __name__ == "__main__":
    main()
