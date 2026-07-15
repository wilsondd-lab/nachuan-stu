#!/usr/bin/env python3
"""
纳川图解 · HTML 转 PNG 渲染脚本
=================================

用法：
    python3 render_png.py <输入HTML路径> <输出PNG路径> [选项]

选项：
    --width WIDTH     输出宽度（默认：1080）
    --height HEIGHT   输出高度（默认：1920）
    --wait MS         等待页面加载时间（毫秒，默认：500）
    --engine ENGINE   渲染引擎：auto/chrome/hyperframes/pyppeteer（默认：auto）

示例：
    python3 render_png.py input.html output.png
    python3 render_png.py diagram.html result.png --wait 1000

功能：
    1. 自动检测 Node.js / npx 环境
    2. 优先使用 HyperFrames CLI 渲染
    3. 如果不可用，尝试使用 pyppeteer（Puppeteer Python版）
    4. 都不可用时给出清晰的安装指引
"""

import sys
import os
import shutil
import subprocess
import argparse
import platform
from pathlib import Path


# ============================================================
# 颜色输出
# ============================================================
class Colors:
    """终端颜色输出"""
    RESET = '\033[0m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'

    @classmethod
    def disable(cls):
        """禁用颜色（Windows 旧版或非终端环境）"""
        cls.RESET = ''
        cls.RED = ''
        cls.GREEN = ''
        cls.YELLOW = ''
        cls.BLUE = ''
        cls.CYAN = ''
        cls.BOLD = ''


# 非终端环境或 Windows 旧版禁用颜色
if not sys.stdout.isatty() or platform.system() == 'Windows':
    Colors.disable()


def print_error(msg):
    print(f"{Colors.RED}{Colors.BOLD}[错误]{Colors.RESET} {msg}", file=sys.stderr)


def print_warning(msg):
    print(f"{Colors.YELLOW}{Colors.BOLD}[警告]{Colors.RESET} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}[信息]{Colors.RESET} {msg}")


def print_success(msg):
    print(f"{Colors.GREEN}{Colors.BOLD}[成功]{Colors.RESET} {msg}")


def print_step(msg):
    print(f"\n{Colors.CYAN}{Colors.BOLD}→ {msg}{Colors.RESET}")


# ============================================================
# 环境检测
# ============================================================
def check_node():
    """检测 Node.js 是否可用"""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_info(f"Node.js 已安装：{version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def check_npx():
    """检测 npx 是否可用"""
    try:
        result = subprocess.run(
            ['npx', '--version'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_info(f"npx 已安装：{version}")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return False


def check_hyperframes():
    """检测 HyperFrames CLI 是否可用（通过 npx）"""
    try:
        # 用 npx hyperframes --version 检测，首次运行会自动下载
        result = subprocess.run(
            ['npx', '--yes', 'hyperframes', '--version'],
            capture_output=True, text=True, timeout=120  # 首次下载需要时间
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            print_info(f"HyperFrames CLI 可用：{version}")
            return True
        else:
            # 可能是命令不存在或安装失败
            if 'not found' in result.stderr.lower() or 'command not found' in result.stderr.lower():
                return False
            # 其他错误也视为不可用
            print_warning(f"HyperFrames 检测异常：{result.stderr.strip()[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print_warning("HyperFrames 下载超时，可能是网络问题")
        return False
    except FileNotFoundError:
        return False


def check_pyppeteer():
    """检测 pyppeteer（Python 版 Puppeteer）是否可用"""
    try:
        import pyppeteer  # noqa: F401
        print_info("pyppeteer 已安装")
        return True
    except ImportError:
        return False


def find_chrome():
    """查找本机 Chrome/Chromium 可执行文件。"""
    candidates = []
    system = platform.system()

    if system == 'Darwin':
        candidates.extend([
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            '/Applications/Chromium.app/Contents/MacOS/Chromium',
        ])
    elif system == 'Windows':
        for base in (os.environ.get('PROGRAMFILES'), os.environ.get('PROGRAMFILES(X86)'), os.environ.get('LOCALAPPDATA')):
            if base:
                candidates.extend([
                    os.path.join(base, 'Google', 'Chrome', 'Application', 'chrome.exe'),
                    os.path.join(base, 'Chromium', 'Application', 'chrome.exe'),
                ])

    candidates.extend(filter(None, [
        shutil.which('google-chrome'),
        shutil.which('google-chrome-stable'),
        shutil.which('chromium'),
        shutil.which('chromium-browser'),
    ]))

    return next((path for path in candidates if os.path.isfile(path)), None)


def render_with_chrome(html_path, output_path, width=1080, height=1920, wait_ms=500):
    """使用本机 Chrome/Chromium 无头模式渲染。"""
    chrome_path = find_chrome()
    if not chrome_path:
        return False

    print_step("使用本机 Chrome 渲染...")
    cmd = [
        chrome_path,
        '--headless=new',
        '--disable-gpu',
        '--hide-scrollbars',
        f'--window-size={width},{height}',
        f'--virtual-time-budget={max(wait_ms, 100)}',
        f'--screenshot={output_path}',
        Path(html_path).resolve().as_uri(),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print_success(f"渲染成功！输出文件：{output_path}（{file_size / 1024:.1f} KB）")
            return True
        print_warning(f"本机 Chrome 渲染失败：{result.stderr.strip()[:300]}")
        return False
    except (subprocess.TimeoutExpired, OSError) as exc:
        print_warning(f"本机 Chrome 渲染异常：{exc}")
        return False


# ============================================================
# 渲染引擎：HyperFrames
# ============================================================
def render_with_hyperframes(html_path, output_path, width=1080, height=1920, wait_ms=500):
    """使用 HyperFrames CLI 渲染"""
    print_step("使用 HyperFrames 渲染...")

    # 构建命令
    cmd = [
        'npx', '--yes', 'hyperframes', 'snapshot',
        html_path,
        '-o', output_path,
        '--width', str(width),
        '--height', str(height),
        '--wait', str(wait_ms),
    ]

    print_info(f"命令：{' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )

        if result.returncode == 0:
            # 检查输出文件是否存在
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print_success(f"渲染成功！输出文件：{output_path}（{file_size / 1024:.1f} KB）")
                return True
            else:
                print_error("命令执行成功，但输出文件不存在")
                if result.stdout:
                    print_info(f"stdout: {result.stdout.strip()[:300]}")
                return False
        else:
            print_error(f"渲染失败，退出码：{result.returncode}")
            if result.stderr:
                # 过滤掉 npm 的下载进度信息，只保留关键错误
                error_lines = [
                    line for line in result.stderr.strip().split('\n')
                    if line and not line.startswith('npm ') and '⠋' not in line
                    and '⠙' not in line and '⠹' not in line and '⠸' not in line
                    and '⠼' not in line and '⠴' not in line and '⠦' not in line
                    and '⠧' not in line and '⠇' not in line and '⠏' not in line
                ]
                if error_lines:
                    print_error("错误信息：")
                    for line in error_lines[:10]:
                        print(f"  {line}")
            return False

    except subprocess.TimeoutExpired:
        print_error("渲染超时（超过 120 秒）")
        return False
    except Exception as e:
        print_error(f"渲染异常：{e}")
        return False


# ============================================================
# 渲染引擎：pyppeteer（fallback）
# ============================================================
def render_with_pyppeteer(html_path, output_path, width=1080, height=1920, wait_ms=500):
    """使用 pyppeteer 渲染（fallback）"""
    print_step("使用 pyppeteer 渲染...")

    try:
        import asyncio
        from pyppeteer import launch

        async def _render():
            browser = await launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            page = await browser.newPage()
            await page.setViewport({'width': width, 'height': height})

            # 读取 HTML 文件内容
            html_url = 'file://' + os.path.abspath(html_path)
            await page.goto(html_url, {'waitUntil': 'networkidle0'})

            # 等待额外时间（字体加载等）
            await asyncio.sleep(wait_ms / 1000.0)

            # 截图
            await page.screenshot({'path': output_path, 'fullPage': False})

            await browser.close()

        asyncio.get_event_loop().run_until_complete(_render())

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            print_success(f"渲染成功！输出文件：{output_path}（{file_size / 1024:.1f} KB）")
            return True
        else:
            print_error("输出文件不存在")
            return False

    except ImportError:
        print_error("pyppeteer 未安装")
        return False
    except Exception as e:
        print_error(f"pyppeteer 渲染失败：{e}")
        return False


# ============================================================
# 安装指引
# ============================================================
def print_install_guide(missing_tool):
    """打印缺失工具的安装指引"""
    print()
    print(f"{Colors.BOLD}{Colors.YELLOW}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}  缺少必要工具：{missing_tool}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'=' * 60}{Colors.RESET}")
    print()

    if missing_tool == 'Node.js':
        print(f"{Colors.BOLD}安装方法：{Colors.RESET}")
        print()
        print("  1. 访问 https://nodejs.org 下载 LTS 版本")
        print("  2. 双击安装包，按提示完成安装")
        print("  3. 安装完成后，重启终端运行：")
        print(f"     {Colors.CYAN}node --version{Colors.RESET}")
        print("     如果输出版本号，说明安装成功")
        print()
        print(f"{Colors.BOLD}macOS 用户也可以用 Homebrew：{Colors.RESET}")
        print(f"     {Colors.CYAN}brew install node{Colors.RESET}")
        print()

    elif missing_tool == 'HyperFrames':
        print(f"{Colors.BOLD}安装方法：{Colors.RESET}")
        print()
        print("  HyperFrames 通过 npx 自动安装，首次运行会自动下载。")
        print()
        print(f"{Colors.BOLD}如果下载慢，可以切换 npm 国内镜像：{Colors.RESET}")
        print(f"     {Colors.CYAN}npm config set registry https://registry.npmmirror.com{Colors.RESET}")
        print()
        print("  然后重新运行本脚本即可。")
        print()

    elif missing_tool == 'pyppeteer':
        print(f"{Colors.BOLD}安装方法：{Colors.RESET}")
        print()
        print(f"  {Colors.CYAN}pip install pyppeteer{Colors.RESET}")
        print(f"  {Colors.CYAN}python -m pyppeteer-install{Colors.RESET}")
        print()
        print("  注意：pyppeteer 需要下载 Chromium，约 100-200 MB。")
        print()


# ============================================================
# 主流程
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description='纳川图解 · HTML 转 PNG 渲染工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python3 render_png.py input.html output.png
  python3 render_png.py diagram.html result.png --wait 1000
  python3 render_png.py card.png out.png --width 1080 --height 1920
        """
    )
    parser.add_argument('input', help='输入 HTML 文件路径')
    parser.add_argument('output', help='输出 PNG 文件路径')
    parser.add_argument('--width', type=int, default=1080, help='输出宽度（默认：1080）')
    parser.add_argument('--height', type=int, default=1920, help='输出高度（默认：1920）')
    parser.add_argument('--wait', type=int, default=500, help='等待页面加载毫秒数（默认：500）')
    parser.add_argument('--engine', default='auto', choices=['auto', 'chrome', 'hyperframes', 'pyppeteer'],
                        help='渲染引擎（默认：auto，自动选择）')

    args = parser.parse_args()

    # 打印欢迎信息
    print()
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}  纳川图解 · HTML 转 PNG 渲染工具{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 50}{Colors.RESET}")
    print()

    # 检查输入文件
    html_path = os.path.abspath(args.input)
    if not os.path.exists(html_path):
        print_error(f"输入文件不存在：{html_path}")
        sys.exit(1)

    if not html_path.lower().endswith('.html'):
        print_warning("输入文件不是 .html 后缀，仍将尝试渲染")

    # 确保输出目录存在
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        print_info(f"创建输出目录：{output_dir}")

    print_info(f"输入文件：{html_path}")
    print_info(f"输出文件：{output_path}")
    print_info(f"输出尺寸：{args.width} × {args.height}")

    # 根据引擎选择渲染方式
    if args.engine == 'chrome':
        if not find_chrome():
            print_error("未找到本机 Chrome 或 Chromium")
            sys.exit(1)
        success = render_with_chrome(
            html_path, output_path,
            width=args.width, height=args.height, wait_ms=args.wait
        )
        if not success:
            print_error("本机 Chrome 渲染失败")
            sys.exit(1)

    elif args.engine == 'hyperframes':
        # 强制使用 HyperFrames
        print_step("检测环境...")
        if not check_node():
            print_install_guide('Node.js')
            sys.exit(1)
        if not check_npx():
            print_error("npx 不可用，请重新安装 Node.js")
            sys.exit(1)
        success = render_with_hyperframes(
            html_path, output_path,
            width=args.width, height=args.height, wait_ms=args.wait
        )
        if not success:
            print_error("HyperFrames 渲染失败")
            sys.exit(1)

    elif args.engine == 'pyppeteer':
        # 强制使用 pyppeteer
        print_step("检测环境...")
        if not check_pyppeteer():
            print_install_guide('pyppeteer')
            sys.exit(1)
        success = render_with_pyppeteer(
            html_path, output_path,
            width=args.width, height=args.height, wait_ms=args.wait
        )
        if not success:
            print_error("pyppeteer 渲染失败")
            sys.exit(1)

    else:
        # 自动选择：优先本机 Chrome，避免额外下载 Chromium；再尝试其他引擎
        print_step("检测渲染环境...")

        chrome_path = find_chrome()
        if chrome_path:
            print_info(f"检测到本机浏览器：{chrome_path}")
            success = render_with_chrome(
                html_path, output_path,
                width=args.width, height=args.height, wait_ms=args.wait
            )
            if success:
                sys.exit(0)
            print_warning("本机 Chrome 渲染失败，尝试其他引擎...")

        node_ok = check_node()
        if not node_ok:
            print_warning("未检测到 Node.js")

        # 尝试 HyperFrames
        hyperframes_ok = False
        if node_ok and check_npx():
            hyperframes_ok = check_hyperframes()

        if hyperframes_ok:
            success = render_with_hyperframes(
                html_path, output_path,
                width=args.width, height=args.height, wait_ms=args.wait
            )
            if success:
                sys.exit(0)
            print_warning("HyperFrames 渲染失败，尝试 pyppeteer...")

        # 尝试 pyppeteer
        if check_pyppeteer():
            success = render_with_pyppeteer(
                html_path, output_path,
                width=args.width, height=args.height, wait_ms=args.wait
            )
            if success:
                sys.exit(0)

        # 都不行
        print()
        print(f"{Colors.RED}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}  无法渲染：没有可用的渲染引擎{Colors.RESET}")
        print(f"{Colors.RED}{Colors.BOLD}{'=' * 60}{Colors.RESET}")
        print()

        if not node_ok:
            print_install_guide('Node.js')
        else:
            print(f"{Colors.BOLD}推荐方案（最简单）：{Colors.RESET}")
            print()
            print("  确保 Node.js 已安装，然后运行：")
            print(f"  {Colors.CYAN}npx hyperframes --version{Colors.RESET}")
            print()
            print("  首次运行会自动下载 HyperFrames CLI。")
            print()
            print(f"{Colors.BOLD}备选方案：安装 pyppeteer{Colors.RESET}")
            print()
            print(f"  {Colors.CYAN}pip install pyppeteer{Colors.RESET}")
            print(f"  {Colors.CYAN}python -m pyppeteer-install{Colors.RESET}")
            print()

        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
