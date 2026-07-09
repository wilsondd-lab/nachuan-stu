#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纳川教学视频配音管线：storyboard.json → 分段 TTS 音频 + durations.json

用法:
    python3 tts.py <storyboard.json> [--outdir audio] [--provider auto|minimax|say|sapi|pyttsx3|text]
                       [--voice <voice_id>] [--speed 1.0] [--model speech-02-hd]

Provider:
    auto     (默认) 自动选择, 按优先级 fallback:
             Minimax API → macOS say → Windows SAPI → pyttsx3 → 纯文本时长估算
    minimax  Minimax T2A v2, 需要环境变量 MINIMAX_API_KEY  (全平台, 质量最好)
             可选: MINIMAX_GROUP_ID   (部分账号需要, 作为 ?GroupId= 查询参数)
                   MINIMAX_API_HOST   (默认 https://api.minimaxi.com)
                   MINIMAX_TTS_MODEL  (默认 speech-02-hd)
    say      macOS 内置 TTS (Tingting 音色), 零配置开箱即用  (仅 macOS)
    sapi     Windows PowerShell System.Speech, 零配置开箱即用  (仅 Windows)
    pyttsx3  Python pyttsx3 库, 跨平台, 需 pip install pyttsx3  (全平台)
    text     纯文本时长估算 (中文约 4 字/秒), 生成无声音频骨架  (全平台兜底)

输出 (写入 --outdir):
    seg-01.mp3 ... seg-07.mp3    每段旁白音频 (text 模式为静音占位)
    durations.json               每段音频时长 + 场景时间轴 (start/duration/audio_start)

时间轴规则 (与 index.html 模板约定一致):
    场景时长 = HEAD_PAD(转场+起口) + 音频时长 + TAIL_PAD(收尾停顿), 不低于该段 min_duration
    音频起点 = 场景起点 + HEAD_PAD
"""

import argparse
import binascii
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HEAD_PAD = 0.6   # 场景开头留给转场 + 起口
TAIL_PAD = 0.9   # 旁白结束后的画面停留
DEFAULT_MIN_DURATION = 5.0

# 教学场景推荐音色 (Minimax 系统音色)
#   女声: female-chengshu (成熟知性) / female-yujie (御姐) / presenter_female (女主持)
#   男声: male-qn-jingying (精英青年) / male-qn-daxuesheng (大学生) / presenter_male (男主持)
DEFAULT_VOICE = "female-chengshu"
# macOS say 默认音色 (中文女声, 清晰自然)
DEFAULT_SAY_VOICE = "Tingting"
# 纯文本估算语速 (中文字符/秒)
CHARS_PER_SECOND = 4.0


def log(msg):
    print(msg, flush=True)


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Provider: Minimax T2A v2  (全平台, Python 标准库实现, 无第三方依赖)
# ---------------------------------------------------------------------------
def tts_minimax(text, out_path, voice_id, speed, model):
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        die("MINIMAX_API_KEY 未设置。导出后重试, 或改用其他 provider。")

    host = os.environ.get("MINIMAX_API_HOST", "https://api.minimaxi.com").rstrip("/")
    url = f"{host}/v1/t2a_v2"
    group_id = os.environ.get("MINIMAX_GROUP_ID")
    if group_id:
        url += f"?GroupId={group_id}"

    payload = {
        "model": model,
        "text": text,
        "stream": False,
        "language_boost": "Chinese",
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": speed,
            "vol": 1.0,
            "pitch": 0,
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            status = body.get("base_resp", {}).get("status_code")
            if status != 0:
                msg = body.get("base_resp", {}).get("status_msg", "unknown")
                # 1004 = 鉴权失败, 2013 = 参数错误 — 重试无意义
                if status in (1004, 2013):
                    die(f"Minimax 返回错误 status_code={status}: {msg}")
                raise RuntimeError(f"status_code={status}: {msg}")
            audio_hex = body.get("data", {}).get("audio")
            if not audio_hex:
                raise RuntimeError("响应缺少 data.audio")
            out_path.write_bytes(binascii.unhexlify(audio_hex))
            return
        except (urllib.error.URLError, RuntimeError, ValueError) as e:
            last_err = e
            wait = 2 * (attempt + 1)
            log(f"   ⚠ 第 {attempt + 1} 次调用失败 ({e}), {wait}s 后重试...")
            time.sleep(wait)
    die(f"Minimax TTS 连续失败: {last_err}")


# ---------------------------------------------------------------------------
# Provider: macOS `say`  (零配置, 仅 macOS)
# ---------------------------------------------------------------------------
def tts_say(text, out_path, voice_id, speed, model):
    # 如果用户指定了 Minimax 音色名, 自动 fallback 到 Tingting
    voice = voice_id if voice_id and not voice_id.startswith(("male-", "female-", "presenter", "moss_")) else DEFAULT_SAY_VOICE
    aiff = out_path.with_suffix(".aiff")
    # say 语速: 默认 ~180 wpm, 教学场景放慢一点
    rate = int(180 * speed)
    subprocess.run(["say", "-v", voice, "-r", str(rate), "-o", str(aiff), text], check=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff),
         "-ar", "32000", "-b:a", "128k", str(out_path)],
        check=True,
    )
    aiff.unlink()


# ---------------------------------------------------------------------------
# Provider: Windows PowerShell System.Speech  (零配置, 仅 Windows)
# ---------------------------------------------------------------------------
def tts_sapi(text, out_path, voice_id, speed, model):
    """用 PowerShell 调用 System.Speech.Synthesis 生成 WAV, 再转 MP3.

    零配置: Windows 自带 System.Speech 程序集, 无需安装任何东西.
    中文文本通过临时 UTF-8 文件传递, 避免命令行编码问题.
    """
    # 语速映射: speed 1.0 → rate 0; 范围 -10 ~ 10
    rate = int(round((speed - 1.0) * 10))
    rate = max(-10, min(10, rate))

    # 用临时文件传递中文文本, 避免 PowerShell 命令行编码问题
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", encoding="utf-8", delete=False) as f:
        f.write(text)
        txt_path = Path(f.name)

    wav_path = out_path.with_suffix(".wav")

    try:
        ps_script = f'''
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = {rate}
# 尝试选择用户指定的音色; 找不到就用系统默认
if ('{voice_id}' -ne '' -and '{voice_id}' -ne 'default') {{
    try {{
        $speak.SelectVoice('{voice_id}')
    }} catch {{ }}
}}
$speak.SetOutputToWaveFile('{wav_path}')
$txt = [System.IO.File]::ReadAllText('{txt_path}', [System.Text.Encoding]::UTF8)
$speak.Speak($txt)
$speak.Dispose()
'''
        # 用 -Command 执行, 输出捕获以便排错
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            die(f"PowerShell SAPI TTS 失败: {result.stderr.strip()}")
        if not wav_path.exists():
            die("PowerShell SAPI TTS 未生成 WAV 文件")

        # 转 MP3
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
             "-ar", "32000", "-b:a", "128k", str(out_path)],
            check=True,
        )
    finally:
        # 清理临时文件
        try:
            txt_path.unlink()
        except OSError:
            pass
        try:
            if wav_path.exists():
                wav_path.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# Provider: pyttsx3  (跨平台, 需 pip install pyttsx3)
# ---------------------------------------------------------------------------
def tts_pyttsx3(text, out_path, voice_id, speed, model):
    """用 pyttsx3 库生成 WAV, 再转 MP3. 跨平台但需要 pip 安装."""
    try:
        import pyttsx3
    except ImportError:
        die("pyttsx3 未安装。请运行: pip install pyttsx3")

    wav_path = out_path.with_suffix(".wav")

    engine = pyttsx3.init()
    # 语速: 默认 ~200 wpm
    engine.setProperty("rate", int(200 * speed))
    # 尝试选择指定音色
    if voice_id and voice_id != "default":
        try:
            engine.setProperty("voice", voice_id)
        except Exception:
            pass
    engine.save_to_file(text, str(wav_path))
    engine.runAndWait()
    engine.stop()

    if not wav_path.exists():
        die("pyttsx3 未生成 WAV 文件")

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
         "-ar", "32000", "-b:a", "128k", str(out_path)],
        check=True,
    )
    wav_path.unlink()


# ---------------------------------------------------------------------------
# Provider: 纯文本时长估算  (全平台兜底, 生成静音占位音频)
# ---------------------------------------------------------------------------
def tts_text(text, out_path, voice_id, speed, model):
    """按字数估算音频时长, 生成静音 MP3 占位文件.

    中文按 CHARS_PER_SECOND 字/秒估算. 这样即使没有任何 TTS 引擎,
    也能走通整个管线, 生成视频骨架, 用户后续替换音频即可.
    """
    # 估算时长 (秒) = 字数 / (语速 * 基准字速)
    char_count = len(text.strip())
    estimated_dur = max(1.0, char_count / (CHARS_PER_SECOND * speed))
    estimated_dur = round(estimated_dur, 2)

    # 用 ffmpeg 生成静音 MP3, 让下游管线完全兼容
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error",
         "-f", "lavfi", "-i", "anullsrc=r=32000:cl=mono",
         "-t", str(estimated_dur),
         "-b:a", "128k", str(out_path)],
        check=True,
    )


# ---------------------------------------------------------------------------
# Provider 注册表 & 自动检测
# ---------------------------------------------------------------------------
PROVIDERS = {
    "minimax": tts_minimax,
    "say": tts_say,
    "sapi": tts_sapi,
    "pyttsx3": tts_pyttsx3,
    "text": tts_text,
}

PROVIDER_LABELS = {
    "minimax": "Minimax TTS (API)",
    "say": "macOS say (Tingting)",
    "sapi": "Windows SAPI (PowerShell)",
    "pyttsx3": "pyttsx3 (Python 库)",
    "text": "纯文本时长估算 (静音占位)",
}


def detect_available_providers():
    """按优先级检测当前系统可用的 TTS 引擎, 返回 provider name 列表.

    优先级:
    1. Minimax API (有 MINIMAX_API_KEY 环境变量时)
    2. macOS say (Darwin 系统)
    3. Windows SAPI (Windows 系统, PowerShell + System.Speech)
    4. pyttsx3 (如果已安装)
    5. 纯文本时长估算 (永远可用, 兜底)
    """
    available = []

    # 1. Minimax API
    if os.environ.get("MINIMAX_API_KEY"):
        available.append("minimax")

    # 2. macOS say
    if platform.system() == "Darwin":
        available.append("say")

    # 3. Windows SAPI (检测 PowerShell 是否可用)
    if platform.system() == "Windows":
        # Windows 上 PowerShell 是自带的, System.Speech 也是自带的
        available.append("sapi")

    # 4. pyttsx3 (检测是否已安装)
    try:
        import pyttsx3  # noqa: F401
        available.append("pyttsx3")
    except ImportError:
        pass

    # 5. 纯文本估算 (永远可用)
    available.append("text")

    return available


def resolve_provider(requested):
    """根据请求和环境变量自动选择 TTS 引擎."""
    if requested == "auto" or requested is None:
        providers = detect_available_providers()
        return providers[0]  # 优先级最高的可用引擎
    return requested


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storyboard", help="storyboard.json 路径")
    ap.add_argument("--outdir", default="audio", help="音频输出目录 (默认 audio/)")
    ap.add_argument("--provider",
                    choices=["auto", "minimax", "say", "sapi", "pyttsx3", "text"],
                    default="auto",
                    help="TTS 引擎 (auto=自动按优先级 fallback)")
    ap.add_argument("--voice", default=None, help="音色 id (默认取 storyboard.voice.voice_id)")
    ap.add_argument("--speed", type=float, default=None, help="语速 (默认 1.0)")
    ap.add_argument("--model", default=None,
                    help="Minimax 模型 (默认取 MINIMAX_TTS_MODEL 或 speech-02-hd)")
    args = ap.parse_args()

    sb_path = Path(args.storyboard)
    if not sb_path.exists():
        die(f"找不到 {sb_path}")
    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    segments = sb.get("segments")
    if not segments:
        die("storyboard.json 缺少 segments 数组")

    voice_cfg = sb.get("voice", {})
    provider = resolve_provider(args.provider or voice_cfg.get("provider", "auto"))
    voice_id = args.voice or voice_cfg.get("voice_id", DEFAULT_VOICE)
    speed = args.speed if args.speed is not None else float(voice_cfg.get("speed", 1.0))
    model = args.model or os.environ.get("MINIMAX_TTS_MODEL", "speech-02-hd")

    if provider not in PROVIDERS:
        die(f"未知 provider: {provider}. 可用: {', '.join(PROVIDERS.keys())}")
    tts = PROVIDERS[provider]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    label = PROVIDER_LABELS.get(provider, provider)
    log(f"==> TTS: provider={provider} ({label})")
    log(f"    voice={voice_id}  speed={speed}"
        + (f"  model={model}" if provider == "minimax" else ""))

    # 显示可用引擎列表, 方便用户了解 fallback 链
    all_available = detect_available_providers()
    log(f"    当前系统可用引擎 (按优先级): {' → '.join(all_available)}")

    if provider == "text":
        log(f"    ⚠ 纯文本估算模式: 生成静音占位音频, 时长按 {CHARS_PER_SECOND} 字/秒估算")
        log(f"    如需真实配音, 请设置 MINIMAX_API_KEY 或安装可用的 TTS 引擎")
    elif provider == "minimax":
        log(f"    使用 Minimax 高清 TTS, 全平台兼容")
    elif provider == "say":
        log(f"    使用 macOS 内置 TTS (零配置开箱即用)")
    elif provider == "sapi":
        log(f"    使用 Windows 内置 SAPI (零配置开箱即用)")
    elif provider == "pyttsx3":
        log(f"    使用 pyttsx3 (需已 pip install pyttsx3)")

    cursor = 0.0
    results = []
    for seg in segments:
        sid = seg["id"]
        narration = seg["narration"].strip()
        out_path = outdir / f"seg-{sid:02d}.mp3"
        log(f"   [{sid}/{len(segments)}] {seg.get('title', '')} ({len(narration)} 字)")
        tts(narration, out_path, voice_id, speed, model)
        audio_dur = round(probe_duration(out_path), 2)

        min_dur = float(seg.get("min_duration", DEFAULT_MIN_DURATION))
        scene_dur = round(max(HEAD_PAD + audio_dur + TAIL_PAD, min_dur), 2)
        results.append({
            "id": sid,
            "title": seg.get("title", ""),
            "file": f"{outdir.name}/{out_path.name}",
            "audio_duration": audio_dur,
            "start": round(cursor, 2),
            "audio_start": round(cursor + HEAD_PAD, 2),
            "duration": scene_dur,
            "subtitle": narration,
        })
        cursor += scene_dur

    manifest = {
        "topic": sb.get("topic", ""),
        "provider": provider,
        "voice_id": voice_id,
        "head_pad": HEAD_PAD,
        "tail_pad": TAIL_PAD,
        "total": round(cursor, 2),
        "segments": results,
    }
    manifest_path = outdir / "durations.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    log(f"✅ {len(results)} 段音频 → {outdir}/  总时长 {manifest['total']}s")
    log(f"✅ 时间轴 → {manifest_path}  (把 segments 的 start/duration/audio_start 抄进 index.html)")


if __name__ == "__main__":
    main()
