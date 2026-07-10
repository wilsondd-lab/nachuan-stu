# 配音说明 · Audio Guide

> 5 级 fallback 配音方案，全平台兼容，零配置可用。
> 配了 API 效果更好，不配也能完整出片。

---

## 五级 Fallback 链

自动检测当前系统可用的最佳引擎，优先级从高到低：

| 优先级 | 引擎 | 支持系统 | 音质 | 需要配置 | 说明 |
|:---:|------|---------|------|:-------:|------|
| 1 | **Minimax TTS** | 全平台 | 高清 | 需要 API Key | 设置 `MINIMAX_API_KEY` 环境变量自动启用 |
| 2 | **macOS say** | macOS 仅 | 一般 | 零配置 | Tingting 中文女声，系统自带 |
| 3 | **Windows SAPI** | Windows 仅 | 一般 | 零配置 | PowerShell + System.Speech，系统自带 |
| 4 | **pyttsx3** | 全平台 | 一般 | 需 pip 安装 | `pip install pyttsx3`，跨平台离线 TTS |
| 5 | **纯文本时长估算** | 全平台 | 无音频 | 零配置 | 按字数估算时长，生成静音占位音频 |

> **默认 auto 模式**：自动按上表优先级选择第一个可用引擎。
> 脚本运行时会打印当前系统的完整 fallback 链，方便排查。

---

## 各引擎详解

### 1. Minimax TTS（全平台，推荐）

**触发条件**：检测到 `MINIMAX_API_KEY` 环境变量时自动启用。

**特点**：
- 高清自然音色，接近真人朗读
- 支持多种音色和情感
- 中文发音标准，断句自然
- 按字符计费，约 0.01 元 / 千字（非常便宜）

**配置方式**：
```bash
# macOS / Linux
export MINIMAX_API_KEY=你的API密钥

# Windows PowerShell
$env:MINIMAX_API_KEY = "你的API密钥"
```

**可选环境变量**：
- `MINIMAX_GROUP_ID` — 部分账号需要，作为查询参数
- `MINIMAX_TTS_MODEL` — 默认 `speech-02-hd`
- `MINIMAX_VOICE_ID` — 音色 ID，默认 `female-chengshu`

**推荐音色**：
| 音色 ID | 性别 | 风格 | 适用场景 |
|---------|------|------|---------|
| `female-chengshu` | 女 | 成熟知性 | 通用教学（默认） |
| `presenter_female` | 女 | 播报风格 | 正式讲解 |
| `male-qn-jingying` | 男 | 青年精英 | 理科教学 |
| `presenter_male` | 男 | 播报风格 | 正式讲解 |

**适用场景**：正式发布、追求高质量、批量生产

---

### 2. macOS say（零配置，macOS 专属）

**触发条件**：运行在 macOS 上，检测到 `say` 命令。

**特点**：
- 零配置：macOS 系统自带，不需要任何 API Key
- 中文女声：Tingting（普通话，清晰自然）
- 离线可用：不需要网络
- 速度快：本地生成，几乎即时完成

**音色列表**（macOS 自带中文）：
- `Tingting` — 普通话女声（默认，推荐）
- `Sinji` — 粤语女声
- `Meijia` — 台湾普通话女声

**手动测试**：
```bash
say -v Tingting "你好，这是一个测试"
```

**输出格式**：
- 直接输出 AIFF，脚本自动用 ffmpeg 转 MP3
- 采样率 22050Hz，单声道

**适用场景**：快速预览、教学内容验证、无 API Key 时的完整产出

---

### 3. Windows SAPI（零配置，Windows 专属）

**触发条件**：运行在 Windows 上，检测到 PowerShell + System.Speech。

**特点**：
- 零配置：Windows 系统自带，不需要安装任何东西
- 通过 PowerShell 调用 `System.Speech.Synthesis.SpeechSynthesizer`
- 音色取决于系统安装的语音包（通常有 Huihui / Yaoyao 等中文语音）

**手动测试**（PowerShell）：
```powershell
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Speak("你好，这是一个测试")
```

**输出格式**：
- 生成 WAV 文件，脚本自动用 ffmpeg 转 MP3
- 采样率 22050Hz，单声道

**适用场景**：Windows 用户零配置快速预览

---

### 4. pyttsx3（跨平台，可选安装）

**触发条件**：检测到已安装 `pyttsx3` Python 包。

**特点**：
- 纯 Python 离线 TTS 库
- 跨平台：macOS / Windows / Linux
- 调用系统自带的语音引擎
- 安装简单：`pip install pyttsx3`

**安装方式**：
```bash
pip install pyttsx3
```

**适用场景**：Linux 环境、不想用系统 TTS 时的离线方案

---

### 5. 纯文本时长估算（全平台兜底）

**触发条件**：以上所有引擎都不可用时自动启用。

**特点**：
- 永远可用，不需要任何引擎或 API
- 按中文字数估算时长（约 4.5 字/秒）
- 用 ffmpeg 生成静音 MP3 占位文件
- 生成完整的时间轴 `durations.json`，下游管线完全兼容

**时长估算公式**：
```
时长(秒) = 中文字符数 / 4.5 + 0.5（首尾留白）
```

**适用场景**：
- Linux 服务器环境
- 快速搭建项目骨架
- 后续再替换真实音频
- 只需要画面不需要声音的预览

---

## 输出文件结构

```
project_dir/
└── audio/
    ├── seg-01.mp3        # 第 1 段旁白
    ├── seg-02.mp3        # 第 2 段旁白
    ├── ...
    ├── seg-07.mp3        # 第 7 段旁白
    └── durations.json    # 时间轴数据（唯一真相来源）
```

### durations.json 格式

```json
{
  "total": 72.5,
  "engine": "macos_say",
  "segments": [
    {
      "id": 1,
      "text": "很多人以为速度快就是加速度大...",
      "duration": 8.2,
      "start": 0.6,
      "audio_start": 0.6
    },
    {
      "id": 2,
      "text": "先说速度。速度描述物体运动的快慢...",
      "duration": 9.5,
      "start": 8.8,
      "audio_start": 8.8
    }
  ]
}
```

**字段说明**：
- `total`：总时长（秒）
- `engine`：使用的配音引擎
- `segments[].duration`：本段旁白时长
- `segments[].start`：本段在时间轴上的开始时间
- `segments[].audio_start`：音频开始播放的时间（含入场前的间隙）

> **重要**：`durations.json` 是视频时间轴的唯一来源。
> 所有场景时长、字幕时间、转场时间都从这里来，不要手抄数字。

---

## 字幕同步原理

1. TTS 生成每段音频，同时记录每段时长
2. 把各段时长累加，生成完整时间轴
3. 字幕入场时间 = 段开始时间 + 0.6s 偏移
4. 字幕退场时间 = 下一段开始时间 - 0.4s
5. 转场时间 = 下一段开始时间（模糊叠化 0.5s）

这样字幕和配音天然同步，不需要手动对齐。

---

## 常见问题

### Q：为什么不直接用系统 TTS 还要 fallback？
A：不同平台可用的 TTS 不一样。macOS 有 say，Windows 有 SAPI，Linux 啥都没有。五级 fallback 保证不管什么平台都能工作。

### Q：Minimax 配音贵吗？
A：非常便宜。一分钟视频约 150 字，费用约 0.0015 元。做 100 个视频才一块多。

### Q：可以用其他 TTS 服务吗？
A：可以。只要最终生成 `audio/seg-XX.mp3` 和 `audio/durations.json` 就行，格式对得上就能用。

### Q：配音质量不好怎么办？
A：
1. 优先配 Minimax API Key，音质提升最大
2. 系统 TTS 的话，macOS 的 Tingting 比 Windows 默认语音好
3. 文案尽量口语化、短句，机器读出来更自然
4. 可以调整语速（默认 1.0，推荐 0.95-1.05）

### Q：怎么改配音语速？
A：设置环境变量 `TTS_RATE`，如 `export TTS_RATE=0.95`（稍慢更清晰）。

### Q：Linux 上怎么用？
A：
- 有网络 + Minimax Key → 用 Minimax（音质最好）
- 装了 pyttsx3 + 系统有语音包 → 用 pyttsx3
- 都没有 → 自动用纯文本时长估算（无音频，但时间轴完整）
