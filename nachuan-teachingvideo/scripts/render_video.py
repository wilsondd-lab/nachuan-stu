#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_video.py — 纳川教学视频渲染脚本

调用 npx hyperframes render 渲染视频，输入项目目录，输出 MP4。
带错误处理和友好提示。

用法:
    python3 render_video.py <项目目录>
    python3 render_video.py <项目目录> --output <输出文件名>
    python3 render_video.py <项目目录> --mode silent  # 无声动图模式
    python3 render_video.py <项目目录> --lint-only    # 只做 lint 检查

示例:
    python3 render_video.py my-video
    python3 render_video.py my-video --output speed-vs-acceleration.mp4
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path


# ── 颜色输出（终端不支持时自动降级） ──────────────────────────────
def _supports_color():
    """检测终端是否支持彩色输出。"""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


_color_ok = _supports_color()


def _c(text, color):
    """给文字加颜色。"""
    if not _color_ok:
        return text
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "cyan": "\033[96m",
        "bold": "\033[1m",
        "dim": "\033[2m",
    }
    reset = "\033[0m"
    return f"{colors.get(color, '')}{text}{reset}"


def info(msg):
    print(f"{_c('ℹ', 'blue')}  {msg}")


def success(msg):
    print(f"{_c('✓', 'green')}  {msg}")


def warn(msg):
    print(f"{_c('⚠', 'yellow')}  {msg}")


def error(msg):
    print(f"{_c('✗', 'red')}  {msg}", file=sys.stderr)


def step(msg):
    print(f"\n{_c('→', 'cyan')}  {_c(msg, 'bold')}")


# ── 环境检测 ─────────────────────────────────────────────────────

def check_node():
    """检测 Node.js 是否安装。"""
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_npx():
    """检测 npx 是否可用。"""
    try:
        result = subprocess.run(
            ["npx", "--version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_hyperframes():
    """检测 HyperFrames CLI 是否可用（通过 npx）。"""
    try:
        result = subprocess.run(
            ["npx", "hyperframes", "--version"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        # 有些版本没有 --version，用 --help 检测
        result2 = subprocess.run(
            ["npx", "hyperframes", "--help"],
            capture_output=True, text=True, timeout=30
        )
        if result2.returncode == 0:
            return True, "可用（版本未知）"
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def check_ffmpeg():
    """检测 ffmpeg 是否可用。"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            # 提取版本号第一行
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        return False, ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, ""


def run_environment_check():
    """运行完整环境检测，打印能力卡片。"""
    print(_c("┌─────────────────────────────────────────┐", "dim"))
    print(_c("│     纳川教学视频 · 环境能力检测          │", "bold"))
    print(_c("└─────────────────────────────────────────┘", "dim"))
    print()

    all_ok = True

    # Node.js
    ok, ver = check_node()
    if ok:
        success(f"Node.js 已安装: {ver}")
    else:
        error("Node.js 未安装")
        warn("  → 请访问 https://nodejs.org 下载安装（推荐 LTS 版本）")
        all_ok = False

    # npx
    ok, ver = check_npx()
    if ok:
        success(f"npx 已安装: {ver}")
    else:
        error("npx 不可用")
        all_ok = False

    # HyperFrames
    ok, ver = check_hyperframes()
    if ok:
        success(f"HyperFrames 可用: {ver}")
    else:
        warn("HyperFrames 首次运行时会自动下载（npx 会处理）")
        warn("  → 如果网络较慢，可能需要等待几分钟")

    # ffmpeg
    ok, ver = check_ffmpeg()
    if ok:
        success(f"ffmpeg 已安装")
    else:
        error("ffmpeg 未安装")
        warn("  → macOS: brew install ffmpeg")
        warn("  → Windows: 从 https://ffmpeg.org/download.html 下载")
        warn("  → Linux: sudo apt install ffmpeg")
        all_ok = False

    print()
    if all_ok:
        success(_c("环境检测全部通过！可以开始渲染视频。", "bold"))
    else:
        warn(_c("环境有缺失，请先安装上述工具后再使用。", "bold"))
        print()
        info("提示：Node.js 和 ffmpeg 是必需的，HyperFrames 会自动通过 npx 安装。")

    return all_ok


# ── 渲染核心 ─────────────────────────────────────────────────────

def find_index_html(project_dir: Path) -> Path:
    """在项目目录中查找 index.html。"""
    index_file = project_dir / "index.html"
    if index_file.exists():
        return index_file

    # 如果项目目录本身就是 HTML 文件
    if project_dir.is_file() and project_dir.suffix == ".html":
        return project_dir

    return None


def run_lint(project_dir: Path) -> bool:
    """运行 HyperFrames lint 检查。"""
    step("运行 Lint 检查")

    cmd = ["npx", "hyperframes", "lint", "."]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(project_dir.parent) if project_dir.is_file() else str(project_dir),
            capture_output=True, text=True, timeout=120
        )

        # 输出结果
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            success("Lint 检查通过")
            return True
        else:
            # 检查是否只有 warning 没有 error
            if "error" in result.stdout.lower() or "error" in result.stderr.lower():
                error("Lint 检查发现错误，请修复后再渲染")
                return False
            else:
                warn("Lint 有警告但无错误，可以继续渲染")
                return True

    except subprocess.TimeoutExpired:
        error("Lint 检查超时（超过 2 分钟）")
        return False
    except FileNotFoundError:
        error("无法运行 npx hyperframes lint")
        return False


def run_validate(project_dir: Path) -> bool:
    """运行 HyperFrames validate 检查。"""
    step("运行结构验证")

    work_dir = project_dir.parent if project_dir.is_file() else project_dir
    cmd = ["npx", "hyperframes", "validate", "."]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(work_dir),
            capture_output=True, text=True, timeout=120
        )

        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # 只在有错误时打印 stderr
            if "error" in result.stderr.lower():
                print(result.stderr, file=sys.stderr)

        if result.returncode == 0:
            success("结构验证通过")
            return True
        else:
            error("结构验证失败，请检查 HTML 结构")
            return False

    except subprocess.TimeoutExpired:
        warn("验证超时（可能是 CDN 加载慢），跳过验证继续渲染")
        return True  # 验证不是硬门槛
    except FileNotFoundError:
        error("无法运行 npx hyperframes validate")
        return False


def run_render(project_dir: Path, output_path: Path, mode: str = "video") -> bool:
    """调用 HyperFrames 渲染视频。"""
    step(f"开始渲染（模式: {mode}）")

    work_dir = project_dir.parent if project_dir.is_file() else project_dir
    output_name = output_path.name

    cmd = [
        "npx", "hyperframes", "render", ".",
        "--output", str(output_path),
    ]

    # 无声模式：设置 mode 变量
    if mode == "silent":
        cmd.extend(["--variables", '{"mode":"silent"}'])

    info(f"输出文件: {output_path}")
    info("渲染中，请耐心等待（60秒视频约需 1-3 分钟）...")
    print()

    try:
        # 实时输出进度
        process = subprocess.Popen(
            cmd,
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            # 过滤掉一些过于冗长的日志
            stripped = line.strip()
            if stripped:
                print(stripped)

        process.wait()

        print()
        if process.returncode == 0:
            success(f"渲染完成！输出文件: {output_path}")

            # 显示文件大小
            if output_path.exists():
                size_mb = output_path.stat().st_size / (1024 * 1024)
                info(f"文件大小: {size_mb:.1f} MB")

            return True
        else:
            error(f"渲染失败，退出码: {process.returncode}")
            return False

    except FileNotFoundError:
        error("无法运行 npx hyperframes render")
        error("请确认 Node.js 已安装，并且可以访问 npm 仓库")
        return False
    except KeyboardInterrupt:
        warn("用户中断渲染")
        return False


# ── 主流程 ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="纳川教学视频 · 渲染脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 render_video.py my-video-project
  python3 render_video.py my-video --output result.mp4
  python3 render_video.py my-video --mode silent
  python3 render_video.py --check-env        # 只检测环境
        """
    )
    parser.add_argument(
        "project", nargs="?", default=".",
        help="项目目录路径（包含 index.html）"
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="输出文件名（默认: renders/output.mp4）"
    )
    parser.add_argument(
        "--mode", "-m", default="video",
        choices=["video", "silent"],
        help="输出模式: video（配音视频）或 silent（无声动图），默认 video"
    )
    parser.add_argument(
        "--check-env", action="store_true",
        help="只检测环境，不渲染"
    )
    parser.add_argument(
        "--lint-only", action="store_true",
        help="只做 lint 检查，不渲染"
    )
    parser.add_argument(
        "--skip-lint", action="store_true",
        help="跳过 lint 和 validate 检查，直接渲染"
    )
    parser.add_argument(
        "--skip-validate", action="store_true",
        help="跳过 validate 检查"
    )

    args = parser.parse_args()

    # 只检测环境
    if args.check_env:
        ok = run_environment_check()
        sys.exit(0 if ok else 1)

    # 解析项目目录
    project_path = Path(args.project).resolve()

    if not project_path.exists():
        error(f"项目路径不存在: {project_path}")
        sys.exit(1)

    # 查找 index.html
    index_file = find_index_html(project_path)
    if not index_file:
        error(f"找不到 index.html，请确认项目目录正确")
        error(f"  项目路径: {project_path}")
        sys.exit(1)

    info(f"项目目录: {project_path}")
    info(f"入口文件: {index_file}")
    print()

    # 快速环境检测（不打断流程）
    node_ok, _ = check_node()
    if not node_ok:
        error("Node.js 未安装，无法继续")
        info("请先安装 Node.js: https://nodejs.org")
        sys.exit(1)

    # 确定输出路径
    if args.output:
        output_path = Path(args.output).resolve()
    else:
        # 默认输出到项目目录的 renders/ 下
        project_dir = project_path if project_path.is_dir() else project_path.parent
        renders_dir = project_dir / "renders"
        renders_dir.mkdir(exist_ok=True)
        suffix = "" if args.mode == "video" else "-silent"
        output_path = renders_dir / f"output{suffix}.mp4"

    # 只 lint
    if args.lint_only:
        ok = run_lint(project_path)
        sys.exit(0 if ok else 1)

    # ── 渲染流程 ──

    # 1. Lint 检查
    if not args.skip_lint:
        lint_ok = run_lint(project_path)
        if not lint_ok:
            error("Lint 未通过，终止渲染。使用 --skip-lint 可强制跳过（不推荐）。")
            sys.exit(1)

    # 2. Validate 检查
    if not args.skip_lint and not args.skip_validate:
        validate_ok = run_validate(project_path)
        # validate 失败不终止，只警告

    # 3. 渲染
    render_ok = run_render(project_path, output_path, args.mode)

    if render_ok:
        print()
        print(_c("═══════════════════════════════════════════", "green"))
        success(_c("  视频渲染成功！", "bold"))
        print(_c("═══════════════════════════════════════════", "green"))
        print()
        info(f"输出文件: {output_path}")
        print()
    else:
        print()
        error("渲染失败")
        print()
        info("常见问题排查:")
        info("  1. 检查网络连接（首次运行需要下载 HyperFrames）")
        info("  2. 检查 index.html 是否有语法错误")
        info("  3. 运行 --lint-only 查看详细 lint 信息")
        info("  4. 确认 ffmpeg 已安装")
        sys.exit(1)


if __name__ == "__main__":
    main()
