#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重配音后同步时间轴到 index.html。

改了旁白文案或换了音色后，不要手抄新数字，用这个脚本一键同步。

用法:
    python3 sync_timeline.py <project_dir>

会更新 index.html 中的:
    - root 的 data-duration
    - 所有 <audio> 的 data-start / data-duration
    - SEGMENTS_VIDEO 数组的 start/duration/subtitle
"""

import json
import re
import sys
from pathlib import Path


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("用法: python3 sync_timeline.py <project_dir>")
        sys.exit(1)

    proj = Path(sys.argv[1]).resolve()
    dur_path = proj / "audio" / "durations.json"
    html_path = proj / "index.html"

    for p in (dur_path, html_path):
        if not p.exists():
            die(f"找不到 {p}")

    dur = json.loads(dur_path.read_text(encoding="utf-8"))
    segs = dur["segments"]
    html = html_path.read_text(encoding="utf-8")

    # 1. 更新 root data-duration
    html = re.sub(
        r'data-duration="[\d.]+"',
        f'data-duration="{dur["total"]}"',
        html, count=1,
    )

    # 2. 更新 audio 标签的 data-start / data-duration
    # 按顺序替换 <audio ...> 的 data-start 和 data-duration
    for i, seg in enumerate(segs):
        # 替换第 i+1 个 audio 标签
        idx = i + 1
        # 匹配特定 id 的 audio
        pattern = rf'(<audio id="a{idx}"[^>]*data-start=")[\d.]+("[^>]*data-duration=")[\d.]+(")'
        repl = rf'\g<1>{seg["audio_start"]}\g<2>{seg["audio_duration"]}\g<3>'
        html = re.sub(pattern, repl, html)

    # 3. 更新 SEGMENTS_VIDEO 数组
    # 找到 SEGMENTS_VIDEO = [ ... ]; 块
    seg_match = re.search(
        r'(const SEGMENTS_VIDEO = \[)(.*?)(\];)',
        html, re.DOTALL,
    )
    if not seg_match:
        die("找不到 SEGMENTS_VIDEO 数组")

    new_segs = []
    for i, s in enumerate(segs, start=1):
        # 从原数据里拿 transition（如果 durations 里没有就用 blur-crossfade）
        trans = s.get("transition", "blur-crossfade")
        subtitle_escaped = json.dumps(s["subtitle"], ensure_ascii=False)
        new_segs.append(
            f'      {{ sel: "#s{i}", start: {s["start"]}, duration: {s["duration"]}, '
            f'transition: "{trans}",\n        subtitle: {subtitle_escaped} }},'
        )

    new_segs_block = "\n".join(new_segs)
    html = html[:seg_match.start(2)] + "\n" + new_segs_block + "\n    " + html[seg_match.end(2):]

    html_path.write_text(html, encoding="utf-8")
    print(f"✅ 时间轴已同步 → {html_path}")
    print(f"   总时长: {dur['total']}s  场景数: {len(segs)}")
    print("   下一步: 重新渲染")


if __name__ == "__main__":
    main()
