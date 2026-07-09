#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""纳川教学视频配音管线：storyboard.json → 分段 TTS 音频 + durations.json

用法:
    python3 tts.py <storyboard.json> [--outdir audio] [--provider auto|say|minimax]
                       [--voice <voice_id>] [--speed 1.0] [--model speech-02-hd]

Provider:
    auto     (默认) 自动选择: 有 MINIMAX_API_KEY 环境变量时用 minimax, 否则用 say
    say      macOS 内置 TTS (Tingting 音色), 零配置开箱即用
    minimax  Minimax T2A v2, 需要环境变量 MINIMAX_API_KEY
             可选: MINIMAX_GROUP_ID   (部分账号需要, 作为 ?GroupId= 查询参数)
                   MINIMAX_API_HOST   (默认 https://api.minimaxi.com)
                   MINIMAX_TTS_MODEL  (默认 speech-02-hd)

输出 (写入 --outdir):
    seg-01.mp3 ... seg-07.mp3    每段旁白音频
    durations.json               每段音频时长 + 场景时间轴 (start/duration/audio_start)

时间轴规则 (与 index.html 模板约定一致):
    场景时长 = HEAD_PAD(转场+起口) + 音频时长 + TAIL_PAD(收尾停顿), 不低于该段 min_duration
    音频起点 = 场景起点 + HEAD_PAD
"""

import argparse
import binascii
import json
import os
import subprocess
import sys
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


def log(msg):
    print(msg, flush=True)


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Provider: Minimax T2A v2
# ---------------------------------------------------------------------------
def tts_minimax(text, out_path, voice_id, speed, model):
    api_key = os.environ.get("MINIMAX_API_KEY")
    if not api_key:
        die("MINIMAX_API_KEY 未设置。导出后重试, 或用 --provider say 走 macOS 内置 TTS。")

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
# Provider: macOS `say` (零配置开箱即用, 默认引擎)
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


PROVIDERS = {"minimax": tts_minimax, "say": tts_say}


def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(out.stdout.strip())


def resolve_provider(requested):
    """根据请求和环境变量自动选择 TTS 引擎。"""
    if requested == "auto" or requested is None:
        if os.environ.get("MINIMAX_API_KEY"):
            return "minimax"
        return "say"
    return requested


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("storyboard", help="storyboard.json 路径")
    ap.add_argument("--outdir", default="audio", help="音频输出目录 (默认 audio/)")
    ap.add_argument("--provider", choices=["auto", "say", "minimax"], default="auto",
                    help="TTS 引擎 (auto=自动选择, 有 MINIMAX_API_KEY 用 minimax 否则用 say)")
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
    tts = PROVIDERS[provider]

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    log(f"==> TTS: provider={provider} voice={voice_id if provider == 'minimax' else DEFAULT_SAY_VOICE} speed={speed}"
        + (f" model={model}" if provider == "minimax" else ""))
    if provider == "say":
        log(f"   使用 macOS 内置 TTS (零配置开箱即用)")
        log(f"   如需更高音质, 设置 MINIMAX_API_KEY 后自动升级为 Minimax 引擎")

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
