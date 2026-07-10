#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 storyboard.json + audio/durations.json 生成 index.html 骨架。

用法:
    python3 scaffold_video.py <project_dir> [--force]

前置: 项目目录里已有 storyboard.json，且已跑过 tts.py（有 audio/durations.json）。

生成的骨架已填好（不需要手抄任何数字）:
    - 配色（7 套主题，按 storyboard.palette 选）
    - 章节角标 / data-duration / audio 标签 / SEGMENTS 数组 / 字幕 / 转场引擎
    - 7 个场景外壳 + 标准 GSAP 入场编排
    - 从 ../../assets/vendor/gsap.min.js 本地加载 GSAP（离线可用）

AI 只需要做两件事:
    1. 填 s2-s6 的 diagram-zone (SVG) 和 info-card 内容
    2. 调整 scene2()-scene6() 的入场编排
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
VENDOR_GSAP = SKILL_ROOT / "assets" / "vendor" / "gsap.min.js"

# 7 套莫兰迪主题配色
PALETTES = {
    "sound": {
        "primary": "#E8631C", "accent": "#F4A24C", "highlight": "#FFD166",
        "ink": "#22303C", "neutral": "#5E7183", "soft": "#FFFDF6",
        "line": "#9DAEBB", "bg": "#FFF6E5", "series": "#5E7183",
    },
    "light": {
        "primary": "#E89B00", "accent": "#5B9BD5", "highlight": "#FFE680",
        "ink": "#21313F", "neutral": "#5A7284", "soft": "#FFFDF6",
        "line": "#9FB4C2", "bg": "#FFFCF0", "series": "#5A7284",
    },
    "mechanics": {
        "primary": "#D63B26", "accent": "#F08A24", "highlight": "#FFD166",
        "ink": "#26303A", "neutral": "#64748B", "soft": "#FFFDF8",
        "line": "#A3AEBB", "bg": "#FBF5EB", "series": "#64748B",
    },
    "electricity": {
        "primary": "#0D3B66", "accent": "#F4A300", "highlight": "#FFD166",
        "ink": "#26221C", "neutral": "#8A7D6B", "soft": "#FDFDFB",
        "line": "#BCB2A2", "bg": "#FAFCFF", "series": "#8A7D6B",
    },
    "heat": {
        "primary": "#E25822", "accent": "#88B8D8", "highlight": "#FFD166",
        "ink": "#223240", "neutral": "#5E7488", "soft": "#FFFDF8",
        "line": "#9DB0BE", "bg": "#FFF8F0", "series": "#5E7488",
    },
    "biology": {
        "primary": "#2F9E77", "accent": "#E9B44C", "highlight": "#FFE08A",
        "ink": "#232A22", "neutral": "#857A6A", "soft": "#FCFDF9",
        "line": "#B5AB9B", "bg": "#FAFCF5", "series": "#857A6A",
    },
    "math": {
        "primary": "#7A6296", "accent": "#B98A5C", "highlight": "#D8D1E6",
        "ink": "#433D50", "neutral": "#6B7889", "soft": "#FCFAF6",
        "line": "#B9C2CE", "bg": "#F7F3ED", "series": "#6B7889",
    },
}

# 场景标签映射（中文场景名 → 英文模板名）
SCENE_TEMPLATES = {
    "标题": "title", "引入": "title", "开场": "title",
    "对比": "compare", "区别": "compare", "比较": "compare",
    "公式": "formula", "定义": "formula", "推导": "formula",
    "例子": "example", "生活": "example", "应用": "example",
    "测验": "quiz", "问答": "quiz", "思考": "quiz",
    "总结": "summary", "小结": "summary", "回顾": "summary",
}


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def build_css(palette):
    lines = "\n".join(f"      --{k}:   {v};" for k, v in palette.items())
    return f"""    :root {{
{lines}
    }}"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", help="项目目录 (含 storyboard.json + audio/durations.json)")
    ap.add_argument("--force", action="store_true", help="覆盖已存在的 index.html")
    args = ap.parse_args()

    proj = Path(args.project).resolve()
    sb_path = proj / "storyboard.json"
    dur_path = proj / "audio" / "durations.json"
    out_path = proj / "index.html"

    for p in (sb_path, dur_path):
        if not p.exists():
            die(f"找不到 {p}" + (" — 先跑 tts.py" if "durations" in str(p) else ""))

    if out_path.exists() and not args.force:
        die(f"{out_path} 已存在，覆盖用 --force")

    sb = json.loads(sb_path.read_text(encoding="utf-8"))
    dur = json.loads(dur_path.read_text(encoding="utf-8"))
    segs_sb = {s["id"]: s for s in sb["segments"]}
    segs = dur["segments"]
    if len(segs) < 2:
        die(f"期望至少 2 段，durations.json 里有 {len(segs)} 段")

    palette_name = sb.get("palette", "mechanics")
    if palette_name not in PALETTES:
        die(f"未知 palette '{palette_name}', 可选: {', '.join(PALETTES)}")
    palette = PALETTES[palette_name]

    topic = sb.get("topic", "主题")
    chapter = sb.get("chapter", "学科·章节")

    # ---- 计算 GSAP 相对路径 ----
    gsap_rel = os.path.relpath(VENDOR_GSAP, proj)
    # 确保用正斜杠
    gsap_rel = gsap_rel.replace("\\", "/")

    # ---- 场景 HTML ----
    scenes_html = []
    for i, seg in enumerate(segs, start=1):
        sbseg = segs_sb.get(seg["id"], {})
        title = seg.get("title", f"场景{i}")
        visual = sbseg.get("visual", "")

        if i == 1:
            # 标题场景
            pills = "".join(
                f'<span class="pill">{segs_sb.get(j, {}).get("title", f"概念{j-1}")}</span>'
                for j in range(2, min(7, len(segs) + 1))
                if j in segs_sb
            )
            scene = f'''    <!-- ============ 场景 {i}: {title} ============ -->
    <div id="s{i}" class="scene">
      <div class="scene-content" style="flex-direction: column; justify-content: center; gap: 40px;">
        <div id="s{i}-icon" style="height: 190px;">
          <svg viewBox="0 0 420 210" style="height: 190px; overflow: visible;">
            <!-- TODO: 主题图标 -->
          </svg>
        </div>
        <div id="s{i}-title" class="t-hero">{topic}</div>
        <div id="s{i}-pills" style="display: flex; gap: 22px;">{pills}</div>
        <div id="s{i}-tagline" class="t-label">—— 副标题 ——</div>
      </div>
    </div>'''
        elif i == len(segs):
            # 总结场景
            scene = f'''    <!-- ============ 场景 {i}: {title} ============ -->
    <div id="s{i}" class="scene">
      <div class="ghost" data-layout-ignore>{i - 1:02d}</div>
      <div class="section-chip"><span class="num">{i - 1}</span><span class="label">{title}</span></div>
      <div class="scene-content" style="flex-direction: column; justify-content: center; gap: 30px;">
        <div id="s{i}-number" class="t-hero" style="font-size: 150px;">
          <span id="s{i}-number-inner" style="display: inline-block;">核心公式/数字</span>
        </div>
        <div id="s{i}-note" class="t-label" style="font-size: 28px;">注释文字</div>
        <div class="info-card" id="s{i}-card" style="width: 1060px; flex: none;">
          <div class="card-title">本章小结</div>
          <div class="card-body">
            <p>要点一</p>
            <p>要点二</p>
            <p>要点三</p>
          </div>
        </div>
        <div class="summary-bar" id="s{i}-bar">
          <div class="badge"><div class="icon">1</div><div class="name">概念1</div></div>
          <div class="badge"><div class="icon">2</div><div class="name">概念2</div></div>
          <div class="badge"><div class="icon">3</div><div class="name">概念3</div></div>
          <div class="badge"><div class="icon">4</div><div class="name">概念4</div></div>
        </div>
      </div>
    </div>'''
        else:
            # 中间场景（通用模板：左图右卡）
            ghost_num = i - 1
            scene = f'''    <!-- ============ 场景 {i}: {title} ============
         visual: {visual} -->
    <div id="s{i}" class="scene">
      <div class="ghost" data-layout-ignore>{ghost_num:02d}</div>
      <div class="section-chip"><span class="num">{ghost_num}</span><span class="label">{title}</span></div>
      <div class="scene-content">
        <div class="diagram-zone" id="s{i}-diagram">
          <svg viewBox="0 0 900 700" style="width: 100%; height: 100%; overflow: visible;">
            <!-- TODO: SVG 示意图 -->
          </svg>
        </div>
        <div class="card-zone">
          <div class="info-card" id="s{i}-card">
            <div class="card-title">{title}</div>
            <div class="card-body">
              <p>要点一</p>
              <p>要点二</p>
              <p>要点三</p>
            </div>
          </div>
        </div>
      </div>
    </div>'''
        scenes_html.append(scene)

    # ---- 音频标签 ----
    audio_html = "\n".join(
        f'    <audio id="a{s["id"]}" src="{s["file"]}" data-start="{s["audio_start"]}" '
        f'data-duration="{s["audio_duration"]}" data-track-index="2"></audio>'
        for s in segs
    )

    # ---- SEGMENTS 数组 ----
    seg_lines = []
    for i, s in enumerate(segs, start=1):
        trans = segs_sb.get(s["id"], {}).get("transition", "blur-crossfade")
        seg_lines.append(
            f'      {{ sel: "#s{i}", start: {s["start"]}, duration: {s["duration"]}, '
            f'transition: "{trans}",\n        subtitle: {json.dumps(s["subtitle"], ensure_ascii=False)} }},'
        )
    segments_js = "\n".join(seg_lines)

    # ---- 场景编排函数 ----
    builders = []
    for i in range(1, len(segs) + 1):
        if i == 1:
            builders.append(f'''    function scene{i}(t) {{
      tl.fromTo("#s{i}-title", {{ y: 70, opacity: 0 }},
        {{ y: 0, opacity: 1, duration: 0.8, ease: "power3.out" }}, t + 0.2);
      tl.fromTo("#s{i}-icon", {{ scale: 0.6, opacity: 0 }},
        {{ scale: 1, opacity: 1, duration: 0.7, ease: "back.out(1.5)" }}, t + 0.7);
      tl.fromTo("#s{i}-pills .pill", {{ y: 34, opacity: 0 }},
        {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.out", stagger: 0.09 }}, t + 1.2);
      tl.fromTo("#s{i}-tagline", {{ opacity: 0 }},
        {{ opacity: 1, duration: 0.6, ease: "sine.out" }}, t + 1.9);
    }}''')
        elif i == len(segs):
            builders.append(f'''    function scene{i}(t) {{
      tl.fromTo("#s{i}-number", {{ scale: 0.4, opacity: 0 }},
        {{ scale: 1, opacity: 1, duration: 0.8, ease: "back.out(1.6)" }}, t + 0.3);
      tl.fromTo("#s{i}-note", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.5, ease: "sine.out" }}, t + 1.0);
      tl.fromTo("#s{i}-card", {{ y: 60, opacity: 0 }},
        {{ y: 0, opacity: 1, duration: 0.7, ease: "power3.out" }}, t + 1.4);
      tl.fromTo("#s{i}-bar .badge", {{ y: 40, opacity: 0 }},
        {{ y: 0, opacity: 1, duration: 0.5, stagger: 0.12, ease: "back.out(1.5)" }}, t + 2.2);
      tl.to("#s{i}-number-inner", {{ scale: 1.03, transformOrigin: "50% 50%",
        yoyo: true, repeat: -1, duration: 1.8, ease: "sine.inOut" }}, t + 1.4);
      if (MODE !== "silent") {{
        const end = t + SEGMENTS[{i - 1}].duration;
        tl.to("#s{i} .scene-content, #s{i} .section-chip, #chapter",
          {{ opacity: 0, duration: 0.6, ease: "power1.in" }}, end - 0.7);
      }}
    }}''')
        else:
            builders.append(f'''    function scene{i}(t) {{
      // TODO: 编排入场动画
      // 左图先画 → 再标注 → 卡片滑入
      // 参考模板: templates/scene-compare.html, scene-formula.html 等
      tl.fromTo("#s{i}-card", {{ x: 80, opacity: 0 }},
        {{ x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, t + 0.8);
    }}''')

    builders_js = "\n\n".join(builders)
    scene_builders_list = ", ".join(f"scene{i}" for i in range(1, len(segs) + 1))

    # ---- 组合完整 HTML ----
    html = f'''<!DOCTYPE html>
<html lang="zh-CN" data-composition-variables='[{{"id":"mode","type":"enum","label":"输出模式","default":"video","options":[{{"value":"video","label":"视频(带配音字幕)"}},{{"value":"silent","label":"无声MP4(循环)"}}]}}]'>
<!--
  {topic} · 纳川教学视频
  由 scaffold_video.py 生成，时间轴已按 audio/durations.json 填好
  只需填 TODO 的场景内容 + 调整 scene2()-scene{len(segs)-1}() 编排
  模板参考: templates/ 目录
  渲染: bash ../../scripts/render_video.sh .
-->
<head>
  <meta charset="UTF-8" />
  <script src="{gsap_rel}"></script>
  <style>
    @font-face {{ font-family: "Heiti SC"; src: local("Heiti SC"); }}
    @font-face {{ font-family: "PingFang SC"; src: local("PingFang SC"); }}
    @font-face {{ font-family: "Songti SC"; src: local("Songti SC"); }}
    @font-face {{ font-family: "Noto Sans CJK SC"; src: local("Noto Sans CJK SC"); }}

    /* ==== 配色 (palette: {palette_name}) ==== */
{build_css(palette)}

    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      width: 1920px; height: 1080px; overflow: hidden;
      background: var(--bg);
      font-family: "Heiti SC", "PingFang SC", "Noto Sans CJK SC", sans-serif;
      color: var(--ink);
    }}

    /* ==== 场景容器 ==== */
    .scene {{
      position: absolute; top: 0; left: 0;
      width: 1920px; height: 1080px; overflow: hidden;
      background: var(--bg);
    }}
    .scene + .scene {{ opacity: 0; }}
    .scene::before {{
      content: ""; position: absolute; inset: 0;
      background:
        radial-gradient(1100px 700px at 78% 22%, color-mix(in srgb, var(--accent) 11%, transparent), transparent 70%),
        radial-gradient(900px 620px at 10% 90%, color-mix(in srgb, var(--series) 9%, transparent), transparent 72%),
        repeating-linear-gradient(0deg, color-mix(in srgb, var(--line) 13%, transparent) 0 1px, transparent 1px 96px),
        repeating-linear-gradient(90deg, color-mix(in srgb, var(--line) 13%, transparent) 0 1px, transparent 1px 96px),
        repeating-linear-gradient(0deg, color-mix(in srgb, var(--line) 5%, transparent) 0 1px, transparent 1px 24px),
        repeating-linear-gradient(90deg, color-mix(in srgb, var(--line) 5%, transparent) 0 1px, transparent 1px 24px);
    }}
    .scene::after {{
      content: ""; position: absolute; inset: 0; z-index: 10;
      pointer-events: none; mix-blend-mode: multiply; opacity: 0.16;
      background: url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="240" height="240"><filter id="n"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch" seed="7"/><feColorMatrix type="saturate" values="0"/></filter><rect width="240" height="240" filter="url(%23n)" opacity="0.6"/></svg>');
    }}
    .ghost {{
      position: absolute; right: 48px; bottom: -60px; z-index: 0;
      font-family: "Songti SC", serif;
      font-size: 460px; font-weight: 900; line-height: 1;
      color: color-mix(in srgb, var(--series) 14%, transparent);
      letter-spacing: -0.04em; user-select: none;
    }}

    .scene-content {{
      position: relative; z-index: 1; width: 100%; height: 100%;
      padding: 150px 110px 190px;
      display: flex; gap: 70px; align-items: center;
    }}
    .diagram-zone {{ flex: 1.25; height: 100%; position: relative; }}
    .card-zone {{ flex: 1; display: flex; flex-direction: column; gap: 32px; justify-content: center; }}

    /* ==== 组件 ==== */
    #chapter {{
      position: absolute; top: 42px; right: 56px; z-index: 50;
      font-size: 26px; font-weight: 600; letter-spacing: 0.12em;
      color: var(--series);
      padding-bottom: 6px;
      border-bottom: 3px solid color-mix(in srgb, var(--series) 45%, transparent);
    }}

    .section-chip {{
      position: absolute; top: 42px; left: 56px; z-index: 5;
      display: flex; align-items: center; gap: 16px;
    }}
    .section-chip .num {{
      width: 58px; height: 58px; border-radius: 50%;
      background: var(--primary); color: #fff;
      font-size: 30px; font-weight: 800;
      display: flex; align-items: center; justify-content: center;
    }}
    .section-chip .label {{
      background: #fff; border: 1.5px solid color-mix(in srgb, var(--neutral) 40%, transparent);
      border-radius: 16px; padding: 10px 26px;
      font-size: 28px; font-weight: 800;
      box-shadow: 0 4px 18px color-mix(in srgb, var(--ink) 10%, transparent);
    }}

    .info-card {{
      border-radius: 18px; overflow: hidden;
      border: 1.5px solid color-mix(in srgb, var(--neutral) 30%, transparent);
      border-left: 6px solid var(--primary);
      box-shadow: 0 14px 42px color-mix(in srgb, var(--primary) 9%, transparent);
      background: color-mix(in srgb, #fff 88%, var(--soft));
    }}
    .info-card .card-title {{
      color: var(--neutral);
      font-size: 22px; font-weight: 700; letter-spacing: 0.35em;
      margin: 24px 32px 0; padding-bottom: 14px;
      display: flex; align-items: center; gap: 14px;
      border-bottom: 1px solid color-mix(in srgb, var(--neutral) 30%, transparent);
    }}
    .info-card .card-title::before {{
      content: ""; width: 12px; height: 12px; flex: none;
      background: var(--primary);
    }}
    .info-card .card-body {{ padding: 20px 32px 28px; display: flex; flex-direction: column; gap: 14px; }}
    .info-card .card-body p {{
      font-size: 28px; line-height: 1.5;
      padding-left: 24px; position: relative;
    }}
    .info-card .card-body p::before {{
      content: ""; position: absolute; left: 0; top: 16px;
      width: 9px; height: 9px; border-radius: 2px;
      background: color-mix(in srgb, var(--primary) 70%, #fff);
    }}
    .info-card .formula {{
      font-family: "Songti SC", serif;
      font-size: 36px; font-weight: 900; color: var(--primary);
      padding: 10px 0 0; letter-spacing: 0.04em;
    }}

    .summary-bar {{ display: flex; gap: 56px; justify-content: center; }}
    .badge {{ display: flex; flex-direction: column; align-items: center; gap: 12px; }}
    .badge .icon {{
      width: 96px; height: 96px; border-radius: 50%;
      border: 3px solid var(--primary);
      background: color-mix(in srgb, var(--primary) 12%, #fff);
      font-size: 44px; display: flex; align-items: center; justify-content: center;
      color: var(--primary);
    }}
    .badge .name {{ font-size: 24px; font-weight: 700; }}

    .t-hero {{
      font-family: "Songti SC", serif;
      font-size: 140px; font-weight: 900; letter-spacing: 0.01em; color: var(--primary);
      line-height: 1.08;
    }}
    .t-title {{ font-size: 48px; font-weight: 800; }}
    .t-body {{ font-size: 30px; line-height: 1.6; }}
    sup {{ font-size: 0.55em; }}
    .t-label {{ font-size: 24px; font-weight: 600; letter-spacing: 0.35em; color: var(--neutral); }}

    /* ==== 字幕 ==== */
    #subtitle-layer {{
      position: absolute; left: 0; right: 0; bottom: 52px; z-index: 40;
      display: flex; justify-content: center; pointer-events: none;
    }}
    .subtitle {{
      position: absolute; bottom: 0; max-width: 1480px;
      font-size: 32px; line-height: 1.5; font-weight: 600;
      text-align: center; color: var(--ink);
      background: color-mix(in srgb, #fff 88%, transparent);
      border-left: 6px solid var(--primary);
      border-radius: 14px; padding: 14px 32px;
      box-shadow: 0 8px 28px color-mix(in srgb, var(--ink) 12%, transparent);
      opacity: 0;
    }}

    .diagram-zone svg {{ width: 100%; height: 100%; overflow: visible; }}
    .diagram-zone text {{ font-family: inherit; }}
  </style>
</head>
<body>
  <div id="root" data-composition-id="main" data-width="1920" data-height="1080"
       data-start="0" data-duration="{dur["total"]}">

{chr(10).join(scenes_html)}

    <!-- ============ 常驻层 ============ -->
    <div id="chapter">{chapter}</div>
    <div id="subtitle-layer"></div>

    <!-- ============ 旁白音频 ============ -->
{audio_html}
  </div>

  <script>
    window.__timelines = window.__timelines || {{}};
    const tl = gsap.timeline({{ paused: true }});

    /* ==== 输出模式: video / silent ==== */
    const MODE = (window.__hyperframes && window.__hyperframes.getVariables
      ? window.__hyperframes.getVariables().mode : null) || "video";
    const SILENT_SEG = 4.6;

    const SEGMENTS_VIDEO = [
{segments_js}
    ];

    let _acc = 0;
    const SEGMENTS = MODE === "silent"
      ? SEGMENTS_VIDEO.map((s) => {{ const o = {{ ...s, start: _acc, duration: SILENT_SEG }}; _acc += SILENT_SEG; return o; }})
      : SEGMENTS_VIDEO;

    /* ==== 波形 helper ==== */
    function makeWaves() {{
      document.querySelectorAll("[data-wave]").forEach((el) => {{
        const cfg = JSON.parse(el.getAttribute("data-wave"));
        const lambda = cfg.len / cfg.cycles;
        const cycles = cfg.flow ? cfg.cycles + 1 : cfg.cycles;
        const len = cfg.flow ? cfg.len + lambda : cfg.len;
        const n = Math.round((cfg.samples || 160) * (cycles / cfg.cycles));
        const pts = [];
        for (let i = 0; i <= n; i++) {{
          const x = (i / n) * len;
          let y = Math.sin((2 * Math.PI * cycles * i) / n);
          (cfg.harmonics || []).forEach(([mult, w]) => {{
            y += w * Math.sin((2 * Math.PI * cycles * mult * i) / n);
          }});
          pts.push(`${{(cfg.x0 + x).toFixed(1)}},${{(cfg.y0 - cfg.amp * y).toFixed(1)}}`);
        }}
        el.setAttribute("points", pts.join(" "));
        el.dataset.lambda = lambda.toFixed(1);
      }});
    }}
    makeWaves();
    function drawIn(sel, t, dur, ease) {{
      document.querySelectorAll(sel).forEach((el) => {{
        const len = Math.ceil(el.getTotalLength());
        el.style.strokeDasharray = len;
        tl.fromTo(el, {{ strokeDashoffset: len }},
          {{ strokeDashoffset: 0, duration: dur, ease: ease || "power2.inOut" }}, t);
      }});
    }}

    /* ==== 每场景入场编排 ==== */
{builders_js}

    const SCENE_BUILDERS = [{scene_builders_list}];

    /* ================================================================
       通用引擎
       ================================================================ */
    // 字幕
    const subLayer = document.getElementById("subtitle-layer");
    if (MODE !== "silent") SEGMENTS.forEach((seg, i) => {{
      const div = document.createElement("div");
      div.className = "subtitle";
      div.id = "sub-" + (i + 1);
      div.textContent = seg.subtitle;
      subLayer.appendChild(div);
      const tIn = seg.start + (i === 0 ? 0.4 : 0.7);
      const tOut = (i < SEGMENTS.length - 1
        ? SEGMENTS[i + 1].start : seg.start + seg.duration) - 0.25;
      tl.fromTo("#sub-" + (i + 1), {{ opacity: 0, y: 18 }},
        {{ opacity: 1, y: 0, duration: 0.35, ease: "power2.out" }}, tIn);
      tl.to("#sub-" + (i + 1), {{ opacity: 0, duration: 0.25, ease: "power1.in" }}, tOut);
      tl.set("#sub-" + (i + 1), {{ visibility: "hidden" }}, tOut + 0.3);
    }});

    // 转场
    for (let i = 1; i < SEGMENTS.length; i++) {{
      const prev = SEGMENTS[i - 1], cur = SEGMENTS[i];
      const T = cur.start;
      if (prev.transition === "push-up") {{
        tl.to(prev.sel, {{ y: -1080, duration: 0.5, ease: "power3.inOut" }}, T);
        tl.fromTo(cur.sel, {{ y: 1080, opacity: 1 }},
          {{ y: 0, duration: 0.5, ease: "power3.inOut" }}, T);
        tl.set(prev.sel, {{ opacity: 0, visibility: "hidden", y: 0 }}, T + 0.55);
      }} else {{
        tl.to(prev.sel, {{ filter: "blur(10px)", scale: 1.03, opacity: 0, duration: 0.5, ease: "power2.inOut" }}, T);
        tl.fromTo(cur.sel, {{ filter: "blur(10px)", scale: 0.97, opacity: 0 }},
          {{ filter: "blur(0px)", scale: 1, opacity: 1, duration: 0.5, ease: "power2.inOut" }}, T + 0.1);
        tl.set(prev.sel, {{ visibility: "hidden" }}, T + 0.65);
      }}
    }}

    // 场景内容编排
    SCENE_BUILDERS.forEach((fn, i) => fn(SEGMENTS[i].start));

    window.__timelines["main"] = tl;
  </script>
</body>
</html>
'''

    out_path.write_text(html, encoding="utf-8")
    print(f"✅ 骨架 → {out_path}")
    print(f"   配色: {palette_name}  总时长: {dur['total']}s  场景数: {len(segs)}")
    print(f"   GSAP: {gsap_rel} (本地加载，离线可用)")
    print("   下一步: 填场景内容 (SVG + 卡片文字) + 调整入场编排，然后渲染")


if __name__ == "__main__":
    import os
    main()
