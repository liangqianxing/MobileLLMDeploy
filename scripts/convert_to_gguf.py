#!/usr/bin/env python3
"""
封装 llama.cpp 的转换与量化流程，生成 GGUF 模型文件。

先确保已经克隆并编译好 llama.cpp，脚本会调用其中的 `convert.py` 和 `quantize`。

示例：
    python convert_to_gguf.py --repo qwen/Qwen2.5-1.5B-Instruct \
        --llama-cpp-path D:/tools/llama.cpp --dtype fp16 --quant q4_K_M \
        --out ../models/qwen2.5-1.5b
"""

from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(">>>", " ".join(cmd))
    subprocess.run(cmd, check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert Hugging Face models to GGUF using llama.cpp tools.")
    parser.add_argument("--repo", required=True, help="Hugging Face 仓库名称。")
    parser.add_argument(
        "--llama-cpp-path",
        required=True,
        help="本地 llama.cpp 项目路径。",
    )
    parser.add_argument(
        "--dtype",
        default="fp16",
        choices=["fp32", "fp16", "bf16"],
        help="初始导出的浮点精度。",
    )
    parser.add_argument(
        "--quant",
        default="q4_0",
        help="量化模式，例如 q4_0、q4_K_M、q5_K_M 等。",
    )
    parser.add_argument(
        "--out",
        default="./gguf",
        help="输出目录。",
    )
    parser.add_argument(
        "--vocab-only",
        action="store_true",
        help="仅导出 tokenizer/vocab（无需量化）。",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    llama_path = pathlib.Path(args.llama_cpp_path).expanduser().resolve()
    out_dir = pathlib.Path(args.out).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    convert_py = llama_path / "convert.py"
    quant_bin = llama_path / "build" / "bin" / "quantize"
    if sys.platform.startswith("win"):
        quant_bin = quant_bin.with_suffix(".exe")

    if not convert_py.exists():
        raise FileNotFoundError(f"未找到 convert.py: {convert_py}")
    if not args.vocab_only and not quant_bin.exists():
        raise FileNotFoundError(f"未找到 quantize 可执行文件: {quant_bin}")

    # 1. 调用 convert.py 导出 FP 权重
    fp_path = out_dir / "model-fp.gguf"
    convert_cmd = [
        sys.executable,
        str(convert_py),
        "--model",
        args.repo,
        "--outfile",
        str(fp_path),
        "--outtype",
        args.dtype,
    ]
    run(convert_cmd)
    if args.vocab_only:
        print("仅导出 vocab 完成。")
        return

    # 2. 调用 quantize 得到量化模型
    quant_path = out_dir / f"model-{args.quant}.gguf"
    quant_cmd = [
        str(quant_bin),
        str(fp_path),
        str(quant_path),
        args.quant,
    ]
    run(quant_cmd)
    print(f"量化完成：{quant_path}")


if __name__ == "__main__":
    main()
