#!/usr/bin/env python3
"""
基于 MLC-LLM 的一键打包脚本，生成 Android/iOS 可用的模型包。

示例：
    python package_with_mlc.py --repo qwen/Qwen2.5-1.5B-Instruct \
        --quantization q4f16_1 --target android --out ../models/mlc_qwen15b
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - passthrough
        sys.exit(exc.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package LLM with MLC-LLM translate command.")
    parser.add_argument("--repo", required=True, help="Hugging Face 模型仓库，例如 qwen/Qwen2.5-1.5B-Instruct。")
    parser.add_argument(
        "--quantization",
        default="q4f16_1",
        help="量化配置，如 q4f16_1、q4f16_0、fp16 等。",
    )
    parser.add_argument(
        "--target",
        default="android",
        choices=["android", "iphone", "wasm", "metal", "cuda"],
        help="目标平台。",
    )
    parser.add_argument(
        "--out",
        default="./mlc_artifact",
        help="输出目录。",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="自定义模型名称，默认与仓库同名。",
    )
    parser.add_argument(
        "--max-seq-len",
        type=int,
        default=None,
        help="可选：自定义最大序列长度。",
    )
    parser.add_argument(
        "--conv-template",
        default=None,
        help="可选：对话模板，参考 MLC-LLM 文档，例如 'qwen2'。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = pathlib.Path(args.out).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "mlc_llm",
        "translate",
        args.repo,
        "--quantization",
        args.quantization,
        "--target",
        args.target,
        "--artifact-path",
        str(output_dir),
    ]
    if args.model_name:
        cmd += ["--model", args.model_name]
    if args.max_seq_len:
        cmd += ["--max-seq-len", str(args.max_seq_len)]
    if args.conv_template:
        cmd += ["--conv-template", args.conv_template]

    run(cmd)
    print(f"MLC artifact 已生成：{output_dir}")


if __name__ == "__main__":
    main()
