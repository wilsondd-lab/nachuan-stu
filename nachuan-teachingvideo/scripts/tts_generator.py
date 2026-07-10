#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_generator.py — 纳川教学视频配音生成脚本

5 级 fallback 配音生成：
  1. Minimax API → 2. macOS say → 3. Windows SAPI → 4. pyttsx3 → 5. 纯文本时长估算

输入：文本字符串列表 或 storyboard.json
输出：音频文件 + durations.json 时间轴

零配置也能用（系统自带 TTS 或纯文本估算兜底）。
全平台兼容（macOS / Windows / Linux）。

用法:
    # 从文本文件生成（每行一段）
    python3 tts_generator.py --text-file script.txt --outdir audio/

    # 从 storyboard.json 生成（读取 segments[].narration）
    python3 tts_generator.py --storyboard storyboard.json --outdir audio/

    # 直接传文本（多段用 | 分隔）
    python3 tts_generator.py --text "第一段|第二段|第三段" --outdir audio/

    # 指定引擎
    python3 tts_generator.py --storyboard storyboard.json --engine minimax

    # 检测可用引擎
    python3 tts_generator.py --check
"""

import os
import sys
import json
import time
import argparse
import platform
import subprocess
import tempfile
from pathlib import Path


# ── 工具函数 ──────────────────────────────────────────────────────

def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True

_color_ok = _supports_color()

def _c(text, color):
    if not _color_ok:
        return text
    colors = {
        "red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m",
        "blue": "\033[94m", "cyan": "\033[96m", "bold": "\033[1m",
        "dim": "\033[2m",
    }
    return f"{colors.get(color, '')}{text}\033[0m"

def info(msg):  print(f"{_c('ℹ', 'blue')}  {msg}")
def success(msg): print(f"{_c('✓', 'green')}  {msg}")
def warn(msg):  print(f"{_c('⚠', 'yellow')}  {msg}")
def error(msg): print(f"{_c('✗', 'red')}  {msg}", file=sys.stderr)
def step(msg):  print(f"\n{_c('→', 'cyan')}  {_c(msg, 'bold')}")


def count_chinese_chars(text: str) -> int:
    """统计中文字符数（用于时长估算）。"""
    count = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            count += 1
    return count


def estimate_duration(text: str) -> float:
    """估算文本朗读时长（秒）。

    中文约 4.5 字/秒，加上首尾留白。
    """
    # 统计中文 + 非空白字符
    cn_chars = count_chinese_chars(text)
    other_chars = sum(1 for c in text if not c.isspace() and not ('\u4e00' <= c <= '\u9fff'))
    # 中文按 4.5 字/秒，非中文按 8 字符/秒估算
    duration = cn_chars / 4.5 + other_chars / 8.0
    # 加上首尾留白
    duration += 0.5
    return max(1.5, round(duration, 2))


def get_audio_duration(filepath: Path) -> float:
    """用 ffprobe 获取音频时长（秒）。"""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(filepath)
            ],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def generate_silence(duration: float, output_path: Path) -> bool:
    """用 ffmpeg 生成静音音频文件。"""
    try:
        cmd = [
            "ffmpeg", "-y", "-f", "lavfi",
            "-i", f"anullsrc=channel_layout=mono:sample_rate=22050",
            "-t", str(duration),
            "-c:a", "libmp3lame", "-b:a", "64k",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=30)
        return result.returncode == 0 and output_path.exists()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


# ── 引擎检测 ──────────────────────────────────────────────────────

def detect_minimax() -> bool:
    """检测 Minimax API 是否可用。"""
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    return bool(api_key and len(api_key) > 10)


def detect_macos_say() -> bool:
    """检测 macOS say 命令是否可用。"""
    if platform.system() != "Darwin":
        return False
    try:
        result = subprocess.run(
            ["which", "say"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def detect_windows_sapi() -> bool:
    """检测 Windows SAPI 是否可用。"""
    if platform.system() != "Windows":
        return False
    try:
        result = subprocess.run(
            ["powershell", "-Command", "Add-Type -AssemblyName System.Speech; $true"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def detect_pyttsx3() -> bool:
    """检测 pyttsx3 是否安装。"""
    try:
        import pyttsx3
        return True
    except ImportError:
        return False


def detect_ffmpeg() -> bool:
    """检测 ffmpeg 是否可用。"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_available_engines() -> list:
    """按优先级返回可用的引擎列表。"""
    engines = []
    if detect_minimax():
        engines.append(("minimax", "Minimax TTS（高清）", True))
    if detect_macos_say():
        engines.append(("macos_say", "macOS say（系统内置）", True))
    if detect_windows_sapi():
        engines.append(("windows_sapi", "Windows SAPI（系统内置）", True))
    if detect_pyttsx3():
        engines.append(("pyttsx3", "pyttsx3（离线跨平台）", True))
    # 纯文本估算是永远可用的兜底
    engines.append(("text_estimate", "纯文本时长估算（无音频）", True))
    return engines


def print_engine_status():
    """打印所有引擎的检测状态。"""
    print(_c("┌─────────────────────────────────────────┐", "dim"))
    print(_c("│     纳川教学视频 · 配音引擎检测          │", "bold"))
    print(_c("└─────────────────────────────────────────┘", "dim"))
    print()

    engines = [
        ("minimax", "Minimax TTS", detect_minimax(), "需要 MINIMAX_API_KEY"),
        ("macos_say", "macOS say", detect_macos_say(), "macOS 系统自带"),
        ("windows_sapi", "Windows SAPI", detect_windows_sapi(), "Windows 系统自带"),
        ("pyttsx3", "pyttsx3", detect_pyttsx3(), "pip install pyttsx3"),
        ("text_estimate", "纯文本估算", True, "永远可用，无音频"),
    ]

    for key, name, available, note in engines:
        if available:
            success(f"{name:20s} — 可用  ({note})")
        else:
            warn(f"{name:20s} — 不可用 ({note})")

    print()
    best = get_available_engines()[0]
    info(f"当前最佳引擎: {best[1]}")
    print()


# ── TTS 引擎实现 ─────────────────────────────────────────────────

def tts_minimax(text: str, output_path: Path) -> float:
    """Minimax TTS 生成。返回音频时长（秒）。"""
    import urllib.request

    api_key = os.environ.get("MINIMAX_API_KEY")
    group_id = os.environ.get("MINIMAX_GROUP_ID", "")
    api_host = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com")
    voice_id = os.environ.get("MINIMAX_VOICE_ID", "female-chengshu")
    model = os.environ.get("MINIMAX_TTS_MODEL", "speech-02-hd")
    rate = float(os.environ.get("TTS_RATE", "1.0"))

    url = f"{api_host}/v1/t2a_v2"
    if group_id:
        url += f"?GroupId={group_id}"

    payload = json.dumps({
        "model": model,
        "voice_id": voice_id,
        "text": text,
        "speed": rate,
        "output_format": "mp3",
    }).encode("utf-8")

    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if data.get("base_resp", {}).get("status_code", -1) != 0:
            raise Exception(data.get("base_resp", {}).get("status_msg", "未知错误"))

        # 下载音频文件
        audio_url = data.get("data", {}).get("audio_file") or data.get("audio_file")
        if audio_url:
            with urllib.request.urlopen(audio_url, timeout=60) as audio_resp:
                output_path.write_bytes(audio_resp.read())
        else:
            raise Exception("响应中没有音频文件地址")

        # 获取时长
        duration = get_audio_duration(output_path)
        if duration:
            return duration
        return estimate_duration(text)

    except Exception as e:
        raise RuntimeError(f"Minimax TTS 失败: {e}")


def tts_macos_say(text: str, output_path: Path) -> float:
    """macOS say 命令生成。返回音频时长（秒）。"""
    voice = os.environ.get("MACOS_VOICE", "Tingting")
    rate = os.environ.get("TTS_RATE", "")

    # 先生成 AIFF
    with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as f:
        aiff_path = Path(f.name)

    try:
        cmd = ["say", "-v", voice, "-o", str(aiff_path)]
        if rate:
            # say 的 rate 是单词/分钟，中文需要调整
            # 默认约 180 wpm，乘以 rate 系数
            words_per_min = int(180 * float(rate))
            cmd.extend(["-r", str(words_per_min)])
        cmd.append(text)

        result = subprocess.run(cmd, capture_output=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"say 命令失败: {result.stderr.decode('utf-8', errors='ignore')}")

        # 转 MP3（如果 ffmpeg 可用）
        if detect_ffmpeg():
            cmd = [
                "ffmpeg", "-y", "-i", str(aiff_path),
                "-codec:a", "libmp3lame", "-b:a", "64k",
                "-ar", "22050", "-ac", "1",
                str(output_path)
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            if result.returncode != 0:
                raise RuntimeError("ffmpeg 转码失败")
        else:
            # 没有 ffmpeg 就直接输出 AIFF（改后缀）
            output_path = output_path.with_suffix(".aiff")
            import shutil
            shutil.copy2(aiff_path, output_path)

        # 获取时长
        duration = get_audio_duration(output_path)
        if duration:
            return duration
        return estimate_duration(text)

    finally:
        if aiff_path.exists():
            aiff_path.unlink()


def tts_windows_sapi(text: str, output_path: Path) -> float:
    """Windows SAPI 生成。返回音频时长（秒）。"""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav_path = Path(f.name)

    try:
        ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.SetOutputToWaveFile('{wav_path}')
$synth.Speak([string]::new('{text.replace("'", "''")}'))
$synth.Dispose()
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=60
        )
        if result.returncode != 0:
            raise RuntimeError(f"PowerShell SAPI 失败: {result.stderr.decode('utf-8', errors='ignore')}")

        # 转 MP3
        if detect_ffmpeg():
            cmd = [
                "ffmpeg", "-y", "-i", str(wav_path),
                "-codec:a", "libmp3lame", "-b:a", "64k",
                "-ar", "22050", "-ac", "1",
                str(output_path)
            ]
            subprocess.run(cmd, capture_output=True, timeout=30)
        else:
            import shutil
            shutil.copy2(wav_path, output_path.with_suffix(".wav"))

        duration = get_audio_duration(output_path)
        if duration:
            return duration
        return estimate_duration(text)

    finally:
        if wav_path.exists():
            wav_path.unlink()


def tts_pyttsx3(text: str, output_path: Path) -> float:
    """pyttsx3 生成。返回音频时长（秒）。"""
    import pyttsx3

    engine = pyttsx3.init()

    # 设置语速
    rate = float(os.environ.get("TTS_RATE", "1.0"))
    engine.setProperty('rate', int(200 * rate))

    # 尝试设置中文语音
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
            engine.setProperty('voice', voice.id)
            break

    # 保存到文件
    engine.save_to_file(text, str(output_path))
    engine.runAndWait()
    engine.stop()

    duration = get_audio_duration(output_path)
    if duration:
        return duration
    return estimate_duration(text)


def tts_text_estimate(text: str, output_path: Path) -> float:
    """纯文本时长估算 + 静音音频。返回估算时长。"""
    duration = estimate_duration(text)

    # 如果 ffmpeg 可用，生成静音占位音频
    if detect_ffmpeg():
        generate_silence(duration, output_path)
    else:
        # 没有 ffmpeg 也没关系，创建一个空文件（下游只需要时长）
        output_path.touch()

    return duration


# 引擎分发表
ENGINE_FUNCTIONS = {
    "minimax": tts_minimax,
    "macos_say": tts_macos_say,
    "windows_sapi": tts_windows_sapi,
    "pyttsx3": tts_pyttsx3,
    "text_estimate": tts_text_estimate,
}


# ── 主流程 ───────────────────────────────────────────────────────

def load_texts(args) -> list:
    """从各种输入源加载文本列表。"""
    if args.storyboard:
        sb_path = Path(args.storyboard)
        if not sb_path.exists():
            error(f"storyboard 文件不存在: {sb_path}")
            sys.exit(1)
        with open(sb_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        segments = data.get("segments", [])
        texts = [seg.get("narration", "") for seg in segments]
        if not texts:
            error("storyboard 中没有 segments.narration 数据")
            sys.exit(1)
        return texts

    if args.text_file:
        tf_path = Path(args.text_file)
        if not tf_path.exists():
            error(f"文本文件不存在: {tf_path}")
            sys.exit(1)
        with open(tf_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        if not lines:
            error("文本文件为空")
            sys.exit(1)
        return lines

    if args.text:
        texts = [t.strip() for t in args.text.split("|") if t.strip()]
        if not texts:
            error("没有提供文本内容")
            sys.exit(1)
        return texts

    error("请指定输入来源: --storyboard / --text-file / --text")
    sys.exit(1)


def generate_all(texts: list, outdir: Path, engine: str = "auto") -> dict:
    """生成所有段落的音频 + 时间轴。返回 durations 数据。"""
    outdir.mkdir(parents=True, exist_ok=True)

    # 选择引擎
    if engine == "auto":
        available = get_available_engines()
        engine_key = available[0][0]
        engine_name = available[0][1]
    else:
        engine_key = engine
        engine_name = engine
        # 检查指定引擎是否可用
        if engine not in ENGINE_FUNCTIONS:
            error(f"未知引擎: {engine}")
            error(f"可用引擎: {', '.join(ENGINE_FUNCTIONS.keys())}")
            sys.exit(1)

    info(f"使用引擎: {engine_name}")
    info(f"输出目录: {outdir}")
    info(f"段落数量: {len(texts)}")
    print()

    segments = []
    current_time = 0.6  # 第一段开始前留 0.6s 空白

    for i, text in enumerate(texts):
        seg_num = i + 1
        audio_file = outdir / f"seg-{seg_num:02d}.mp3"

        step(f"第 {seg_num} 段 / 共 {len(texts)} 段")
        info(f"文本: {text[:40]}{'...' if len(text) > 40 else ''}")

        try:
            tts_func = ENGINE_FUNCTIONS[engine_key]
            duration = tts_func(text, audio_file)

            # 段间留 0.3s 间隔
            start_time = current_time
            current_time += duration + 0.3

            seg_info = {
                "id": seg_num,
                "text": text,
                "duration": round(duration, 2),
                "start": round(start_time, 2),
                "audio_start": round(start_time, 2),
                "audio_file": f"seg-{seg_num:02d}.mp3",
            }
            segments.append(seg_info)

            success(f"生成完成，时长: {duration:.2f}s")

        except Exception as e:
            error(f"生成失败: {e}")

            # 如果不是最后一个引擎，自动降级
            if engine_key != "text_estimate":
                warn("尝试降级到下一个引擎...")
                engines = get_available_engines()
                current_idx = next((idx for idx, e in enumerate(engines) if e[0] == engine_key), 0)
                if current_idx < len(engines) - 1:
                    next_engine = engines[current_idx + 1]
                    warn(f"降级到: {next_engine[1]}")
                    engine_key = next_engine[0]
                    # 重试当前段
                    try:
                        tts_func = ENGINE_FUNCTIONS[engine_key]
                        duration = tts_func(text, audio_file)
                        start_time = current_time
                        current_time += duration + 0.3
                        segments.append({
                            "id": seg_num,
                            "text": text,
                            "duration": round(duration, 2),
                            "start": round(start_time, 2),
                            "audio_start": round(start_time, 2),
                            "audio_file": f"seg-{seg_num:02d}.mp3",
                        })
                        success(f"降级后生成成功，时长: {duration:.2f}s")
                        continue
                    except Exception as e2:
                        error(f"降级后仍然失败: {e2}")

            # 最终兜底：纯文本估算
            warn("使用纯文本时长估算作为兜底")
            duration = tts_text_estimate(text, audio_file)
            start_time = current_time
            current_time += duration + 0.3
            segments.append({
                "id": seg_num,
                "text": text,
                "duration": round(duration, 2),
                "start": round(start_time, 2),
                "audio_start": round(start_time, 2),
                "audio_file": f"seg-{seg_num:02d}.mp3",
            })
            warn(f"估算时长: {duration:.2f}s（无真实音频）")

    # 计算总时长
    total = round(current_time - 0.3 + 0.5, 2)  # 最后一段结束后留 0.5s

    # 写入 durations.json
    durations_data = {
        "total": total,
        "engine": engine_key,
        "engine_name": engine_name,
        "segment_count": len(segments),
        "segments": segments,
    }

    durations_path = outdir / "durations.json"
    with open(durations_path, "w", encoding="utf-8") as f:
        json.dump(durations_data, f, ensure_ascii=False, indent=2)

    print()
    success(f"全部完成！总时长: {total:.2f}s")
    info(f"时间轴文件: {durations_path}")

    return durations_data


def main():
    parser = argparse.ArgumentParser(
        description="纳川教学视频 · 配音生成脚本（5 级 fallback）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 检测可用引擎
  python3 tts_generator.py --check

  # 从 storyboard.json 生成
  python3 tts_generator.py --storyboard storyboard.json --outdir audio/

  # 直接传文本
  python3 tts_generator.py --text "第一段|第二段" --outdir audio/

  # 指定引擎
  python3 tts_generator.py --storyboard sb.json --engine minimax
        """
    )
    parser.add_argument("--check", action="store_true", help="检测可用引擎")
    parser.add_argument("--storyboard", "-s", help="storyboard.json 文件路径")
    parser.add_argument("--text-file", "-f", help="文本文件路径（每行一段）")
    parser.add_argument("--text", "-t", help="直接传文本（多段用 | 分隔）")
    parser.add_argument("--outdir", "-o", default="audio", help="输出目录（默认: audio/）")
    parser.add_argument(
        "--engine", "-e", default="auto",
        choices=["auto", "minimax", "macos_say", "windows_sapi", "pyttsx3", "text_estimate"],
        help="指定配音引擎（默认 auto 自动选择最佳）"
    )

    args = parser.parse_args()

    # 只检测
    if args.check:
        print_engine_status()
        return

    # 加载文本
    texts = load_texts(args)

    # 生成
    outdir = Path(args.outdir).resolve()
    data = generate_all(texts, outdir, args.engine)

    # 打印摘要
    print()
    print(_c("═══════════════════════════════════════════", "green"))
    success(_c("  配音生成完成", "bold"))
    print(_c("═══════════════════════════════════════════", "green"))
    print()
    info(f"引擎: {data['engine_name']}")
    info(f"段落: {data['segment_count']} 段")
    info(f"总时长: {data['total']:.2f} 秒")
    info(f"输出目录: {outdir}")
    print()


if __name__ == "__main__":
    main()
