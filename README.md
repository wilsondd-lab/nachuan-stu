# 纳川 Skills · 准高中生AI学习伙伴

本仓库包含两个为**准高中生**量身打造的AI学习技能，基于 [linyuebanzi-skills](https://github.com/lqshow/linyuebanzi-skills) 深度改造，融合 OpenMontage 视频制作方法论，结合《准高中生AI橙皮书》教育理念。

---

## Skill 列表

### 1. nachuan-tujie（纳川图解）

**教育信息图生成工具**

- **功能**：将初中全科知识点转化为 9:16 竖版教育信息图
- **学科覆盖**：语文、数学、英语、物理、化学、生物、政治、历史、地理 + 高中预科
- **核心特性**：
  - 🎨 7 套莫兰迪主题配色，学科专属色卡
  - ✅ 双层准确性双保险：生图前自检 + 生图后视觉复核
  - 📚 内置物理/数学/化学/生物等学科的插图指引
  - 🔄 支持批量生成，每章不同色系
- **基础模式**：无需外部生图 API Key；本地渲染需要 Node.js、npx 和首次下载依赖的网络条件
- **高级选项**：支持 MuleRun / APImart / Atlas Cloud 外部生图 API

**触发词**：做一张信息图、知识卡片、学科图解、纳川图解

[查看详情 → `nachuan-tujie/SKILL.md`](nachuan-tujie/SKILL.md)

---

### 2. nachuan-teachingvideo（纳川教学视频）

**动态教学视频生成工具**

- **功能**：将学科概念自动做成动态教学内容
- **两种产出**（共用同一 HTML，双模式切换）：
  - 🎬 **配音教学视频**：1080p、60-90s、中文旁白 + 字幕
  - 🔄 **无声循环动图**：1080p、~32s、无声循环
- **学科覆盖**：物理（声/光/力/电/热）、数学、生物、化学、语文、英语
- **核心特性**：
  - 🎨 7 套主题配色，同学科同色系统一
  - 🎙️ 默认 macOS 内置配音（零配置），可选 Minimax TTS 升级
  - 🎬 HyperFrames 本地渲染，不消耗 token
  - 📐 SVG 矢量示意图，精确可控可动画
  - 📖 融合 OpenMontage 教学叙事方法论
- **基础模式**：无需外部配音 API Key；需要 Node.js、ffmpeg 和本地 HyperFrames 渲染环境

**触发词**：教学视频、配音视频、教学动图、无声动图、循环视频、纳川教学

[查看详情 → `nachuan-teachingvideo/SKILL.md`](nachuan-teachingvideo/SKILL.md)

---

## 设计理念

### 来自《准高中生AI橙皮书》

- **准确性优先**：每张图/视频必须走完知识自检 + 视觉复核两道关
- **S.T.P. 方法**：场景（Scenario）→ 工具（Tool）→ 练习（Practice）
- **亲子共读**：家长和孩子一起学，一起操作
- **碎片学习**：60-90 秒短视频，碎片时间高效吸收

### 来自 OpenMontage（方法论融合）

- **Mayer 多媒体学习原则**
- **讲解型弧线模板**：钩子 → 张力 → 概念 → 核心洞察 → 证明 → 启示 → 收尾
- **误解优先法**：先呈现常见误解再反驳，学习效果更好
- **引导式发现法**：重建推理路径，让学生感觉是自己发现的
- **动效设计四原则**：缓入缓出 / 预备动作 / 超出回弹 / 分层错峰

---

## 安装使用

### 快速安装

```bash
# 安装到 TRAE CN 的全局 skills 目录
npx -y skills add wilsondd-lab/nachuan-stu --skill nachuan-tujie --agent trae-cn --global --yes --copy
npx -y skills add wilsondd-lab/nachuan-stu --skill nachuan-teachingvideo --agent trae-cn --global --yes --copy

# 验证两个 Skill 是否已经出现
npx -y skills list --global --agent trae-cn

# 或直接克隆
git clone https://github.com/wilsondd-lab/nachuan-stu.git
```

基础功能不要求外部 API Key，但本地仍需具备各 Skill 在首次检查中列出的 Node.js、npx、ffmpeg 或渲染组件。首次安装和下载依赖时需要可用网络。

### 生图与配音升级（可选）

如需更高质量的生图或配音，可配置以下环境变量：

```bash
# 生图 API（三选一）
export MULERUN_API_KEY=sk-xxx      # MuleRun Nano Banana 2
export APIMART_API_KEY=sk-xxx       # APImart GPT Image 2
export ATLASCLOUD_API_KEY=sk-xxx  # Atlas Cloud GPT Image 2

# 配音 API（可选）
export MINIMAX_API_KEY=sk-xxx       # Minimax TTS 高清配音
```

---

## 自动更新

本仓库配置了自动同步上游更新机制，每 5 天从 linyuebanzi-skills 上游拉取最新更新，按纳川规范自动改造后更新。

自动更新流程：
1. 拉取上游最新代码
2. 对比差异识别变更
3. 应用纳川改造规则（名字替换、基础模式配置、OpenMontage 融合、橙皮书定位）
4. 提交并推送更新

手动触发更新：
```bash
python3 update_scripts/sync_upstream.py
```

---

## 与上游区别

| 维度 | 上游 linyuebanzi-skills | 纳川 nachuan-stu |
|------|----------------------|-------------------|
| 目标用户 | 通用 | 准高中生 + 家长 |
| 生图配置 | 需要 API Key | 基础模式无需外部生图 API Key，仍需本地渲染环境 |
| 配音配置 | 需要 Minimax API Key | 基础模式可用系统配音，仍需本地视频渲染环境 |
| 教学方法论 | 基础分镜模板 | + OpenMontage 叙事 + 橙皮书理念 |
| Skill 结构 | 分离（业务层/执行层分离） | 合并（一站式） |
| 名字品牌 | 林月半子 | 纳川 |

---

## 许可证

基于上游开源项目改造，遵循上游许可证。
