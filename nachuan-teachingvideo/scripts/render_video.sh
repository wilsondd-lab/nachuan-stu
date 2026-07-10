#!/usr/bin/env bash
# ============================================================
#  render_video.sh — 纳川教学视频一键渲染脚本
# ============================================================
# 用法:
#   bash render_video.sh <project_dir> [output.mp4] [options]
#
# Options:
#   --silent     渲染无声循环动图 (silent 模式, ~32s)
#   --draft      快速草稿渲染 (低质量, 迭代用)
#   --no-lint    跳过 lint 检查 (不推荐)
#   --no-montage 跳过蒙太奇预览图生成
#
# 示例:
#   bash render_video.sh examples/velocity-acceleration
#   bash render_video.sh my-video --silent
#   bash render_video.sh my-video output.mp4 --draft
#
# 输出:
#   <project_dir>/renders/<name>.mp4       (配音视频)
#   <project_dir>/renders/<name>-silent.mp4 (无声动图)
#   <project_dir>/preview/montage.png       (7场景蒙太奇)
# ============================================================

set -euo pipefail

# ---- 工具检测 ----
check_tools() {
  local missing=()

  if ! command -v node &> /dev/null; then
    missing+=("Node.js")
  fi

  if ! command -v ffmpeg &> /dev/null; then
    missing+=("ffmpeg")
  fi

  if ! command -v ffprobe &> /dev/null; then
    missing+=("ffprobe (ffmpeg 的一部分)")
  fi

  if [ ${#missing[@]} -gt 0 ]; then
    echo "❌ 缺少必要工具: ${missing[*]}"
    echo ""
    echo "安装方法:"
    for tool in "${missing[@]}"; do
      case "$tool" in
        Node.js)
          echo "  macOS:   brew install node"
          echo "  Windows: 去 https://nodejs.org 下载安装包"
          echo "  Linux:   sudo apt install nodejs npm"
          ;;
        ffmpeg*)
          echo "  macOS:   brew install ffmpeg"
          echo "  Windows: winget install ffmpeg 或去 https://ffmpeg.org 下载"
          echo "  Linux:   sudo apt install ffmpeg"
          ;;
      esac
    done
    echo ""
    echo "装好之后重新运行即可。"
    exit 1
  fi
}

# ---- 参数解析 ----
if [[ $# -lt 1 ]]; then
  echo "用法: $0 <project_dir> [output.mp4] [--silent] [--draft] [--no-lint] [--no-montage]"
  echo ""
  echo "示例:"
  echo "  $0 examples/velocity-acceleration           # 渲染配音视频"
  echo "  $0 my-video --silent                         # 渲染无声动图"
  echo "  $0 my-video --draft                          # 快速草稿渲染"
  exit 1
fi

PROJECT_DIR=""
OUTPUT=""
MODE="video"       # video | silent
QUALITY="standard" # standard | draft
RUN_LINT=true
RUN_MONTAGE=true

for arg in "$@"; do
  case "$arg" in
    --silent)   MODE="silent" ;;
    --draft)    QUALITY="draft" ;;
    --no-lint)  RUN_LINT=false ;;
    --no-montage) RUN_MONTAGE=false ;;
    -*)
      echo "未知选项: $arg"
      exit 1
      ;;
    *)
      if [[ -z "$PROJECT_DIR" ]]; then
        PROJECT_DIR="$arg"
      else
        OUTPUT="$arg"
      fi
      ;;
  esac
done

# ---- 检测工具 ----
check_tools

# ---- 进入项目目录 ----
cd "$PROJECT_DIR"
PROJECT_DIR=$(pwd)
NAME=$(basename "$(pwd)")

if [[ ! -f index.html ]]; then
  echo "❌ 找不到 index.html，请确认 $PROJECT_DIR 是正确的项目目录"
  exit 1
fi

# ---- 确定输出路径 ----
if [[ -z "$OUTPUT" ]]; then
  if [[ "$MODE" == "silent" ]]; then
    OUTPUT="renders/${NAME}-silent.mp4"
  else
    OUTPUT="renders/${NAME}.mp4"
  fi
fi

mkdir -p renders preview

echo "=========================================="
echo " 纳川教学视频 · 渲染"
echo "=========================================="
echo "项目:   $NAME"
echo "模式:   $MODE ($( [[ $MODE == silent ]] && echo '无声循环动图' || echo '配音视频'))"
echo "质量:   $QUALITY"
echo "输出:   $OUTPUT"
echo "=========================================="
echo ""

# ---- 1. Lint 检查 ----
if $RUN_LINT; then
  echo "==> [1/4] Lint 检查..."
  if ! npx --yes hyperframes lint index.html 2>&1; then
    echo ""
    echo "❌ Lint 检查失败，请修复上面的错误后重试"
    echo "   跳过 lint: 加 --no-lint 参数（不推荐）"
    exit 1
  fi
  echo "   ✅ Lint 通过"
  echo ""
else
  echo "==> [1/4] Lint 检查 (跳过 --no-lint)"
  echo ""
fi

# ---- 2. Validate（警告不阻断） ----
echo "==> [2/4] Validate 验证..."
npx --yes hyperframes validate index.html 2>&1 || echo "   ⚠ validate 有警告（见上），渲染继续 — 对比度问题请回去调色"
echo ""

# ---- 3. 渲染 ----
echo "==> [3/4] 渲染中 ($QUALITY)..."
HF_ARGS=(--quality "$QUALITY" --output "$OUTPUT")

if [[ "$MODE" == "silent" ]]; then
  HF_ARGS+=(--variables '{"mode":"silent"}')
fi

npx --yes hyperframes render "${HF_ARGS[@]}" index.html 2>&1

if [[ ! -f "$OUTPUT" ]]; then
  echo "❌ 渲染失败，没有找到输出文件: $OUTPUT"
  exit 1
fi

FILE_SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
echo "   ✅ 渲染完成 ($FILE_SIZE)"
echo ""

# ---- 4. 蒙太奇预览 ----
if $RUN_MONTAGE; then
  echo "==> [4/4] 生成蒙太奇预览..."
  mkdir -p preview/.frames && rm -f preview/.frames/*.png

  # 取7个时间点：优先按 durations.json 的场景中点，否则7等分
  if [[ -f audio/durations.json ]]; then
    TIMES=$(python3 -c "
import json
d = json.load(open('audio/durations.json'))
segs = d['segments']
# 取前7段，不足则补
while len(segs) < 7:
    segs.append(segs[-1] if segs else {'start': 0, 'duration': 1})
print(' '.join(f\"{s['start'] + s['duration'] / 2:.2f}\" for s in segs[:7]))")
  else
    DUR=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT")
    TIMES=$(python3 -c "
d = float('$DUR')
print(' '.join(f'{d / 7 * (i + 0.5):.2f}' for i in range(7)))")
  fi

  i=1
  for T in $TIMES; do
    ffmpeg -y -loglevel error -ss "$T" -i "$OUTPUT" -frames:v 1 "preview/.frames/f-$i.png" 2>/dev/null || true
    i=$((i + 1))
  done

  MONTAGE_FILE="preview/montage$( [[ $MODE == silent ]] && echo '-silent' || echo '' ).png"
  ffmpeg -y -loglevel error -framerate 1 -i "preview/.frames/f-%d.png" \
    -vf "scale=480:-1,tile=2x4:padding=12" -frames:v 1 -update 1 "$MONTAGE_FILE" 2>/dev/null || true
  rm -rf preview/.frames

  if [[ -f "$MONTAGE_FILE" ]]; then
    echo "   ✅ 蒙太奇 → $MONTAGE_FILE"
  else
    echo "   ⚠ 蒙太奇生成失败（不影响视频）"
  fi
  echo ""
else
  echo "==> [4/4] 蒙太奇预览 (跳过 --no-montage)"
  echo ""
fi

# ---- 完成 ----
DURATION=$(ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "$OUTPUT" 2>/dev/null || echo "?")

echo "=========================================="
echo " ✅ 渲染完成！"
echo "=========================================="
echo " 视频文件: $OUTPUT"
echo " 时长:     ${DURATION}s"
echo " 文件大小: $FILE_SIZE"
if $RUN_MONTAGE && [[ -f "${MONTAGE_FILE:-}" ]]; then
  echo " 预览图:   $MONTAGE_FILE"
fi
echo "=========================================="
