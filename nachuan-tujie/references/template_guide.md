# 模板选用指南

本文档帮助你为不同类型的知识点选择最合适的模板，并说明每种模板的数据格式。

## 快速选择

| 知识点类型 | 推荐模板 | 判断依据 |
|-----------|---------|---------|
| 单个概念/定义讲解 | **概念卡** (concept) | "什么是XX"、"XX的概念"、单一知识点有3-5个要点 |
| 两个概念对比 | **对比卡** (compare) | "XX和YY的区别"、"XX vs YY"、成对出现的概念 |
| 公式/定理 | **公式卡** (formula) | 有核心公式、变量需要解释、有适用条件 |
| 步骤/流程 | **步骤卡** (steps) | "解题步骤"、"实验步骤"、"操作流程"、有明确先后顺序 |
| 时间顺序的事件 | **时间线** (timeline) | 历史事件、发展过程、有明确时间节点 |
| 知识体系/章节总结 | **思维导图** (mindmap) | 章节复习、知识框架、多个子主题围绕一个中心 |

---

## 各模板数据格式

### 1. 概念卡 (concept)

**适用场景**：什么是集合、什么是浮力、什么是光合作用

**JSON 数据格式**：

```json
{
  "subject": "物理",
  "grade": "初二",
  "title": "什么是浮力",
  "subtitle": "液体和气体对浸在其中的物体的作用力",
  "hero_icon": "🌊",
  "definition": "<strong>浮力</strong>是液体或气体对浸在其中的物体产生的<strong>竖直向上</strong>的力。一切浸在液体或气体里的物体都受到浮力。",
  "cards": [
    {
      "number": "01",
      "icon": "⬆️",
      "title": "方向",
      "description": "浮力的方向总是竖直向上的，与重力方向相反。",
      "keywords": {
        "keyword_list": ["竖直向上", "与重力相反"]
      }
    },
    {
      "number": "02",
      "icon": "⚖️",
      "title": "产生原因",
      "description": "物体上下表面存在压力差，向上的压力大于向下的压力。",
      "keywords": {
        "keyword_list": ["压力差", "F向上 > F向下"]
      }
    },
    {
      "number": "03",
      "icon": "📏",
      "title": "阿基米德原理",
      "description": "浮力的大小等于物体排开液体所受的重力，即 F浮 = ρ液gV排。",
      "keywords": {
        "keyword_list": ["F浮=ρ液gV排", "排开液体"]
      }
    },
    {
      "number": "04",
      "icon": "🎯",
      "title": "浮沉条件",
      "description": "浮力大于重力则上浮，等于则悬浮，小于则下沉。",
      "keywords": {
        "keyword_list": ["上浮", "悬浮", "下沉"]
      }
    }
  ],
  "tip": "浮力的施力物体是液体或气体，受力物体是浸在其中的物体。浮力方向永远竖直向上，不是"垂直向上"。",
  "palette": "terracotta"
}
```

**字段说明**：
- `subject` / `grade`：学科和年级，显示在左上角标签
- `title` / `subtitle`：主标题和副标题
- `hero_icon`：核心概念区的图标（emoji）
- `definition`：概念定义，可用 `<strong>` 标签高亮关键词（三段花括号 `{{{definition}}}` 渲染）
- `cards`：要点卡片数组，建议3-5张
  - `number`：卡片编号，显示在右上角做装饰
  - `icon`：卡片图标（emoji）
  - `title` / `description`：标题和描述
  - `keywords.keyword_list`：关键词标签数组（可选）
- `tip`：底部学习提示
- `palette`：主题色（可选，不传则按学科自动匹配）

---

### 2. 对比卡 (compare)

**适用场景**：速度vs加速度、弹力vs摩擦力、光合作用vs呼吸作用

**JSON 数据格式**：

```json
{
  "subject": "物理",
  "grade": "初二",
  "left_title": "速度",
  "right_title": "加速度",
  "subtitle": "描述运动的两个重要物理量",
  "left_icon": "🏃",
  "left_subtitle": "描述运动快慢",
  "right_icon": "🚀",
  "right_subtitle": "描述速度变化快慢",
  "left_items": [
    { "label": "定义", "value": "路程与时间之比" },
    { "label": "公式", "value": "v = s / t" },
    { "label": "单位", "value": "m/s 或 km/h" },
    { "label": "物理意义", "value": "物体运动的快慢" },
    { "label": "标量/矢量", "value": "矢量（有方向）" }
  ],
  "right_items": [
    { "label": "定义", "value": "速度变化量与时间之比" },
    { "label": "公式", "value": "a = Δv / t" },
    { "label": "单位", "value": "m/s²" },
    { "label": "物理意义", "value": "速度变化的快慢" },
    { "label": "标量/矢量", "value": "矢量（有方向）" }
  ],
  "summary": "速度描述物体运动的快慢，加速度描述速度变化的快慢。速度大加速度不一定大（如匀速飞行的飞机），加速度大速度也不一定大（如刚启动的火箭）。",
  "palette": "terracotta"
}
```

**字段说明**：
- `left_title` / `right_title`：左右两侧的概念名称
- `left_icon` / `right_icon`：左右两侧的图标（emoji）
- `left_subtitle` / `right_subtitle`：左右两侧的副标题
- `left_items` / `right_items`：对比项数组，左右数量要对应
  - `label`：属性名称（如"定义""公式"）
  - `value`：属性值
- `summary`：底部核心区别总结
- 建议每侧4-6个对比项

---

### 3. 公式卡 (formula)

**适用场景**：勾股定理、欧姆定律、一元二次方程求根公式

**JSON 数据格式**：

```json
{
  "subject": "数学",
  "grade": "初二",
  "formula_category": "几何定理",
  "formula_title": "勾股定理",
  "formula_content": "a<sup>2</sup> + b<sup>2</sup> = c<sup>2</sup>",
  "formula_description": "直角三角形两条直角边的平方和等于斜边的平方",
  "variables": [
    { "symbol": "a", "name": "直角边", "unit": "长度单位" },
    { "symbol": "b", "name": "直角边", "unit": "长度单位" },
    { "symbol": "c", "name": "斜边", "unit": "长度单位" }
  ],
  "conditions": [
    "只适用于直角三角形",
    "c 必须是斜边（直角的对边）",
    "斜边是三角形中最长的边"
  ],
  "notes": "常见勾股数：3-4-5、5-12-13、8-15-17。它们的整数倍仍然是勾股数。逆定理也成立：若 a²+b²=c²，则三角形为直角三角形。",
  "palette": "purple"
}
```

**字段说明**：
- `formula_category`：公式分类（如"几何定理""物理公式"）
- `formula_title`：公式名称
- `formula_content`：公式内容，用 HTML 标签实现上下标（`<sup>`上标、`<sub>`下标），使用三段花括号渲染
- `formula_description`：公式的一句话解释
- `variables`：变量说明数组
  - `symbol`：变量符号
  - `name`：变量含义
  - `unit`：单位
- `conditions`：适用条件列表（数组形式）
- `notes`：注意事项
- 变量建议4-6个

---

### 4. 步骤卡 (steps)

**适用场景**：解方程步骤、实验步骤、解题五步法

**JSON 数据格式**：

```json
{
  "subject": "数学",
  "grade": "初一",
  "title": "解一元一次方程",
  "subtitle": "五步求解法，按顺序操作",
  "steps": [
    {
      "number": "1",
      "icon": "📝",
      "title": "去分母",
      "description": "方程两边同乘各分母的最小公倍数，消去分母。",
      "detail": "注意：不要漏乘不含分母的项；分子是多项式时要加括号。",
      "has_next": true
    },
    {
      "number": "2",
      "icon": "📐",
      "title": "去括号",
      "description": "按去括号法则去掉括号，注意符号变化。",
      "detail": "括号前是负号时，括号内各项都要变号。",
      "has_next": true
    },
    {
      "number": "3",
      "icon": "↔️",
      "title": "移项",
      "description": "把含未知数的项移到左边，常数项移到右边。",
      "detail": "移项要变号！这是最容易出错的一步。",
      "has_next": true
    },
    {
      "number": "4",
      "icon": "➕",
      "title": "合并同类项",
      "description": "把方程化成 ax = b (a≠0) 的形式。",
      "detail": "系数相加减，字母和指数不变。",
      "has_next": true
    },
    {
      "number": "5",
      "icon": "🎯",
      "title": "系数化为1",
      "description": "方程两边同除以未知数的系数 a，得到 x = b/a。",
      "detail": "注意：除数不能为0，即 a ≠ 0。",
      "has_next": false
    }
  ],
  "summary": "口诀：去分母→去括号→移项→合并同类项→系数化为1。每做完一步，养成检验的好习惯，把解代入原方程验证。",
  "palette": "purple"
}
```

**字段说明**：
- `steps`：步骤数组，建议3-5步
  - `number`：步骤编号（数字或序号文字）
  - `icon`：步骤图标（emoji）
  - `title`：步骤名称
  - `description`：步骤描述
  - `detail`：详细说明/注意事项（可选）
  - `has_next`：是否有下一步（控制箭头显示），最后一步设为 false
- `summary`：底部关键要点总结

---

### 5. 时间线 (timeline)

**适用场景**：历史事件时间线、生物进化、化学反应过程

**JSON 数据格式**：

```json
{
  "subject": "历史",
  "grade": "初一",
  "title": "商鞅变法",
  "subtitle": "战国时期秦国的重要改革",
  "timeline": [
    {
      "side": "left",
      "icon": "📜",
      "date": "公元前356年",
      "event": "开始变法",
      "description": "秦孝公任用商鞅，在秦国推行变法。"
    },
    {
      "side": "right",
      "icon": "🏠",
      "date": "第一次变法",
      "event": "编制户口，奖励耕织",
      "description": "实行连坐法、重农抑商、奖励军功。"
    },
    {
      "side": "left",
      "icon": "📏",
      "date": "公元前350年",
      "event": "第二次变法",
      "description": "废井田开阡陌、推行县制、统一度量衡。"
    },
    {
      "side": "right",
      "icon": "⚔️",
      "date": "变法影响",
      "event": "秦国强大",
      "description": "秦国国力大增，为后来统一六国奠定基础。"
    },
    {
      "side": "left",
      "icon": "💀",
      "date": "公元前338年",
      "event": "商鞅之死",
      "description": "秦孝公死后，商鞅被车裂，但新法继续推行。"
    }
  ],
  "summary": "商鞅变法是战国时期最彻底的一次变法，使秦国一跃成为最强盛的国家。虽然商鞅本人惨死，但"商君死，秦法未败"。",
  "palette": "caramel"
}
```

**字段说明**：
- `timeline`：事件数组，建议4-6个
  - `side`：在时间线的哪一侧，`"left"` 或 `"right"`，建议交替排列
  - `icon`：事件图标（emoji）
  - `date`：时间/日期标签
  - `event`：事件名称
  - `description`：事件描述
- `summary`：底部核心脉络总结

---

### 6. 思维导图 (mindmap)

**适用场景**：章节总结、知识体系梳理

**JSON 数据格式**：

```json
{
  "subject": "物理",
  "grade": "初二",
  "title": "力学知识体系",
  "subtitle": "初中力学核心概念图谱",
  "center_icon": "⚙️",
  "center_text": "力学",
  "connections": [
    { "path": "M480,280 Q300,300 200,200", "color": "#C97E4E" },
    { "path": "M600,300 Q780,320 880,250", "color": "#4A9E9B" },
    { "path": "M680,640 Q800,700 900,650", "color": "#7A6296" },
    { "path": "M400,640 Q200,700 120,650", "color": "#5F6B4F" },
    { "path": "M480,960 Q300,1000 180,950", "color": "#3A506B" }
  ],
  "branch_top": {
    "color": "#C97E4E",
    "icon": "📏",
    "title": "长度与时间",
    "subs": ["刻度尺的使用", "秒表读数", "误差与错误"]
  },
  "branch_top_right": {
    "color": "#4A9E9B",
    "icon": "🏃",
    "title": "运动",
    "subs": ["参照物", "速度公式", "匀速直线运动"]
  },
  "branch_bottom_right": {
    "color": "#7A6296",
    "icon": "💪",
    "title": "力",
    "subs": ["力的三要素", "弹力与重力", "力的示意图"]
  },
  "branch_bottom_left": {
    "color": "#5F6B4F",
    "icon": "⚖️",
    "title": "运动与力",
    "subs": ["牛顿第一定律", "二力平衡", "摩擦力"]
  },
  "branch_top_left": {
    "color": "#3A506B",
    "icon": "🌊",
    "title": "压强与浮力",
    "subs": ["固体压强", "液体压强", "阿基米德原理"]
  },
  "summary": "力学是物理学的基础，从描述运动（运动学）到解释运动的原因（动力学），核心是"力改变物体的运动状态"。",
  "palette": "terracotta"
}
```

**字段说明**：
- `center_icon` / `center_text`：中心节点的图标和文字
- `connections`：SVG 连接线路径数组（可选，纯装饰性）
  - `path`：SVG path 的 d 属性值
  - `color`：线条颜色
- `branch_top` / `branch_top_right` / `branch_bottom_right` / `branch_bottom_left` / `branch_top_left`：五个分支（可选，根据需要启用）
  - `color`：分支颜色
  - `icon`：分支图标（emoji）
  - `title`：分支标题
  - `subs`：子项数组，每分支2-3个
- `summary`：底部学习要点总结

---

## 主题色选择指南

| 学科 | 推荐主题色 | 色值 |
|------|-----------|------|
| 物理（声/热） | terracotta 陶土橙 | #C97E4E |
| 物理（电/力） | slate 深灰蓝 | #3A506B |
| 物理（光/透镜） | teal 柔青绿 | #4A9E9B |
| 化学 | teal 柔青绿 | #4A9E9B |
| 数学 | purple 雾紫 | #7A6296 |
| 生物 | sage 深茶绿 | #5F6B4F |
| 语文 | caramel 焦糖棕 | #8A624A |
| 历史 | caramel 焦糖棕 | #8A624A |
| 英语 | slate 深灰蓝 | #3A506B |
| 地理 | sage-light 鼠尾草绿 | #8FA08A |
| 政治 | slate 深灰蓝 | #3A506B |

**配色规则**：
- 主色只用在标题、编号徽章、关键词、公式高亮上（约10%画面）
- 卡片底和背景走底色的浅变体
- 中性色给次级文字、结构线、说明性标注
- 禁止高饱和糖果色、霓虹色

---

## 数据校验清单

生成 JSON 数据后，按以下清单检查：

- [ ] 必填字段都有值（title、subject 等）
- [ ] 卡片/步骤数量合适（3-5个，不超过6个）
- [ ] 文字长度适中（不会溢出卡片）
- [ ] 公式中的上下标用了正确的 HTML 标签
- [ ] 对比卡左右两侧项目数对应
- [ ] 步骤卡的 has_next 最后一个是 false
- [ ] 时间线的 side 交替排列（视觉平衡）
- [ ] 主题色与学科匹配
- [ ] 知识点内容准确（参考 accuracy_checklist.md）
