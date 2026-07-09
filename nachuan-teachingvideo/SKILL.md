---
name: nachuan-teachingvideo
description: 纳川教学视频 · 准高中生AI学习伙伴。输入一个学科概念（如"声现象""杠杆原理""光合作用"），自动生成动态教学内容。两种产出都由 HyperFrames 本地渲染、共用同一个 index.html（mode 变量切换）：① 配音教学视频 — 7段分镜 + 中文配音（默认 macOS say，可选 Minimax）+ 字幕 + 完整 MP4（1080p，60-90s，适合短视频学习）；② 无声循环动图 — 同一内容的紧凑无声版 MP4（1080p，~32s，循环播放）。共用一套7段分镜结构和7套主题配色（声/光/力/电/热/生物/数学各有色系），视频和动图风格完全统一。当用户提"教学视频""配音视频""教学动图""无声动图""循环视频""概念动画""纳川教学"或给一个学科概念要做成动态内容时，使用本 skill。
---

# 纳川教学视频 · 准高中生AI学习伙伴

## 定位说明

**纳川教学视频**是为准高中生和家长打造的AI学习伙伴，致力于"让抽象概念动起来"。

- **目标用户**：准高中生（初三升高一）+ 家长
- **学科覆盖**：初中全科 + 高中预科（物理、数学、化学、生物、语文、英语）
- **教学理念**：让抽象概念动起来 — 用动态可视化把难懂的知识点讲透
- **视频时长**：默认 60-90 秒，适合短视频学习场景，碎片时间高效吸收
- **语言风格**：亲切、清晰、鼓励性 — 像一位耐心的学长/学姐在讲解
- **开箱即用**：零 API 配置即可生成完整视频（macOS 内置配音 + 本地 HyperFrames 渲染）

---

## 概述

输入一个概念（例："声现象"）→ 两种动态产出，**都是 HyperFrames 本地渲染的 MP4，共用同一个 index.html**：

| 产出 | 规格 | 用途 |
|---|---|---|
| **配音视频** | 1080p、60-90s、中文旁白 + 字幕 | 完整讲解，发视频号 / 给孩子看 |
| **无声动图** | 1080p、~32s、无声、循环 | 公众号内嵌、知识点快速回顾 |

关键：两种产出**共用同一个 `index.html`**，靠 HyperFrames 变量 `mode`（video/silent）切换——
搭一次内容，两种都能出。silent 模式紧凑时间轴、无字幕、不淡出（循环无缝），质感和动效
与视频版完全一致。

共用：**7 段结构**（1 标题 + 5 子概念 + 1 总结）、**同一套主题配色**
（`references/color-palettes.md`）、**同一份分镜脚本**（`references/storyboard-guide.md`）。

---

## 触发路由

| 用户说 | 做什么 |
|---|---|
| "教学视频" / "配音" / "讲解版" / "纳川" | 搭 index.html → `build_video.sh` |
| "教学动图" / "无声" / "循环" / "公众号内嵌" | 搭 index.html → `build_silent.sh` |
| "视频和动图都要" | 搭一次 index.html，两个脚本都跑 |

不确定时，**先问清楚概念 + 适用学段（默认初二物理）**，其他别问。

---

## 配音引擎说明（零配置开箱即用）

### 默认引擎：macOS 内置 say（Tingting 音色）

- **零配置**：不需要任何 API Key，macOS 系统自带
- **音色**：Tingting（中文女声，清晰自然）
- **适用场景**：快速预览、教学内容验证、无 API Key 时的完整产出

### 高级引擎：Minimax TTS（可选升级）

- **触发条件**：设置了 `MINIMAX_API_KEY` 环境变量时自动启用
- **音色选择**：女声 `female-chengshu`（成熟知性）/ `presenter_female`；男声 `male-qn-jingying` / `presenter_male`
- **配置方式**：`export MINIMAX_API_KEY=你的key`，然后正常运行脚本即可
- **适用场景**：正式发布、追求更高音质和表现力

> **注意**：脚本会自动检测环境变量。有 `MINIMAX_API_KEY` 时用 Minimax，没有时自动 fallback 到 macOS say。两种引擎产出的音频格式和时间轴完全兼容，可以随时切换。

---

## 统一流程（两种产出共用前 4 步）

```bash
# 第 0 步：写分镜（见 references/storyboard-guide.md）
#   把概念拆成 7 段，写 storyboard.json：每段 title / narration（旁白 30-50 字，口语化，
#   不读公式）/ visual（画面描述）/ transition。配色按主题族选（color-palettes.md）。
#   拆解质量决定一切 — 对照教材知识点，参考 examples/sound-video/storyboard.json。

# 1. TTS 配音（默认 macOS say，有 MINIMAX_API_KEY 时自动用 Minimax）
python3 scripts/tts.py storyboard.json --outdir audio/
#   → audio/seg-0N.mp3 + audio/durations.json（时间轴来源，无声版也需要它做骨架）

# 2. 生成骨架（时间轴/配色/audio/SEGMENTS/silent机制 全部自动填好，不要手搭）
python3 scripts/scaffold_video.py <project_dir>

# 3. 填场景内容：s2-s6 的 SVG 示意图（零件拷 references/svg-parts.md）+ 卡片文案
#    + scene2()-scene6() 入场编排。规则见 references/video-authoring.md

# 4. 出片（二选一或都要）：
bash scripts/build_video.sh  <project_dir>   # → 配音视频  renders/<name>.mp4
bash scripts/build_silent.sh <project_dir>   # → 无声动图  renders/<name>-silent.mp4
```

`build_video.sh`：lint + WCAG 对比度审计 + render（video 模式）+ 场景中点蒙太奇。
`build_silent.sh`：临时改 data-duration + render（silent 模式，紧凑 32s 无声）+ 蒙太奇。
两个脚本读同一个 index.html，只是渲染的 `mode` 变量不同。

**换音色/改旁白后重跑 TTS，用 `python3 scripts/sync_timeline.py <project_dir>` 同步
时间轴（不要手抄数字），再重新渲染。**

场景内容标准：section-chip + SVG 示意图（≥3 图形元素）+ info-card + callout。
视频尺寸规范、SVG 画法、动效编排、silent 机制、实测 lint 坑都在 `references/video-authoring.md`。

环境：Node.js ≥22 + ffmpeg（`npx hyperframes doctor` 自检）；TTS 默认为 macOS 内置 say，
配置 `MINIMAX_API_KEY` 后自动升级为 Minimax。

---

## silent（无声）模式怎么工作

`index.html` 的 `<html>` 声明 `mode` 变量。渲染时 `--variables '{"mode":"silent"}'` 切到无声版：

- **时间轴**：每段等长紧凑（`SILENT_SEG`=4.6s，共 ~32s），不依赖音频长度
- **无字幕**：`MODE !== "silent"` 才生成字幕
- **不淡出**：最后一段不淡出到底，循环首尾无缝
- **质感动效全保留**：渐变/颗粒/波形流动都在（MP4 有帧间压缩，不像 GIF 怕连续色调和运动）

> 为什么不出 GIF？GIF 无帧间压缩，完整 7 段想要 720p 高清必然 >2MB（实测），只能降到
> 480p 且小字发糊。公众号早已支持内嵌 MP4 自动播放，无声 MP4 = 1080p 完整 + 8~10MB，
> 比任何 GIF 都清晰。所以动图产出用无声 MP4，不用 GIF。

---

## 输出文件规范

```
<topic>/
├── storyboard.json           # 分镜（第 0 步）
├── audio/
│   ├── seg-01..07.mp3         # TTS 分段配音
│   └── durations.json         # 时间轴来源
├── index.html                # HyperFrames 组合（video/silent 双模式）
├── renders/
│   ├── <topic>.mp4            # 配音视频（~60-90s）
│   └── <topic>-silent.mp4     # 无声循环动图（~32s）
└── preview/
    ├── montage.png            # 配音视频蒙太奇
    └── montage-silent.png     # 无声动图蒙太奇
```

---

## 教学方法论

纳川教学视频的内容设计基于以下经过验证的教学原则，详见 `references/teaching-narrative.md`：

- **讲解型弧线模板**：钩子 → 张力 → 概念递进 → 核心洞察 → 验证 → 启示 → 收束
- **Mayer 多媒体学习原则**：分段呈现、信号引导、时空同步、一致性、双通道
- **误解优先法**：先展示常见错误认知，再纠正 — 学习效果提升显著
- **引导式发现法**：不直接给答案，而是重建推理路径，让学习者自己"发现"

---

## 动效设计原则

动效不只是好看，更是为了辅助理解。详见 `references/motion-design.md`：

- **四大核心时序原则**：缓入缓出、预备动作、超出回弹、分层错峰
- **缓动曲线参考表**：出场/入场/强调 各场景的标准 ease 选择
- **停留帧规范**：关键信息展示后的视觉呼吸时间
- **转场类型指南**：模糊叠化（默认）、上推（章节转折）、有限转场家族原则

---

## 质量检查清单

每个教学视频产出前都应通过质量门。详见 `references/quality-checklist.md`：

- **脚本质量门**：知识点准确性、旁白口语化、钩子有效性、概念密度检查
- **分镜质量门**：五维分镜检查（主题/构图/动效/信息密度/转场）
- **最终 QA 清单**：渲染质量、字幕同步、配色合规、文字溢出、音频电平
- **音频设计标准**：旁白清晰度、语速控制、目标 LUFS

---

## 资源

### 核心脚本
- `scripts/tts.py` — 智能 TTS 配音（默认 macOS say，配置 MINIMAX_API_KEY 自动升级）+ 时间轴
- `scripts/scaffold_video.py` — 骨架生成（第 2 步，含 silent 机制）
- `scripts/sync_timeline.py` — 重配音后同步时间轴
- `scripts/build_video.sh` — 配音视频渲染（lint + validate + render + 蒙太奇）
- `scripts/build_silent.sh` — 无声循环动图渲染（silent 模式）

### 模板与示例
- `assets/video-template/index.html` — HyperFrames 模板（组件 + video/silent 双模式 + 转场/字幕/波形引擎）
- `examples/sound-video/` — 声现象完整示例（storyboard → 音频 → index.html → 配音视频 + 无声动图）

### 参考资料
- `references/storyboard-guide.md` — 分镜拆解 + 旁白规范（第 0 步必读）
- `references/video-authoring.md` — 场景编写硬规则 + silent 机制 + 实测坑（必读）
- `references/svg-parts.md` — SVG 符号库（电学/波形/图线/力学/光学，画示意图先来这拷）
- `references/color-palettes.md` — 7 套主题调色板（60-30-10 + 莫兰迪，含 CSS 变量）
- `references/teaching-narrative.md` — 教学叙事方法论（讲解弧线、Mayer 原则、误解优先、引导式发现）
- `references/motion-design.md` — 动效设计原则（时序原则、缓动曲线、停留帧、转场指南）
- `references/quality-checklist.md` — 质量检查清单（脚本质量门、分镜质量门、最终 QA、音频标准）
