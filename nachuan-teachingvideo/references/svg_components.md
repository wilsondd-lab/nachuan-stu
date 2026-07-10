# SVG 动画组件库 · SVG Components

> 可复用的 SVG 动画组件，AI 直接复制粘贴即可。
> 所有组件遵循设计系统配色，可直接嵌入 diagram-zone。

---

## 一、物理类组件

### 1. 小车（侧视图）

```svg
<g id="car" transform="translate(0, 0)">
  <!-- 车身 -->
  <rect x="0" y="30" width="140" height="45" rx="10" fill="var(--primary)"/>
  <!-- 车顶 -->
  <path d="M30,30 L50,0 L110,0 L130,30 Z" fill="var(--primary-deep)"/>
  <!-- 车窗 -->
  <rect x="38" y="8" width="30" height="22" rx="4" fill="#C4DCE8" opacity="0.8"/>
  <rect x="82" y="8" width="30" height="22" rx="4" fill="#C4DCE8" opacity="0.8"/>
  <!-- 车轮 -->
  <circle cx="35" cy="78" r="16" fill="var(--ink)"/>
  <circle cx="35" cy="78" r="7" fill="#888"/>
  <circle cx="115" cy="78" r="16" fill="var(--ink)"/>
  <circle cx="115" cy="78" r="7" fill="#888"/>
</g>
```

**动效建议**：
- 入场：从左/右侧滑入（x 方向平移）
- 行驶：水平移动 + 车轮旋转
- GSAP：`tl.fromTo("#car", {x: -120, opacity: 0}, {x: 0, opacity: 1, duration: 0.9, ease: "power3.out"}, t)`

---

### 2. 速度 / 加速度箭头

```svg
<g id="velocity-arrow">
  <defs>
    <marker id="arrowHead" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto">
      <path d="M0,0 L12,5 L0,10 Z" fill="var(--accent)"/>
    </marker>
  </defs>
  <line x1="0" y1="0" x2="200" y2="0" stroke="var(--accent)" stroke-width="6" stroke-linecap="round" marker-end="url(#arrowHead)"/>
</g>
```

**动效建议**：
- 伸长：`scaleX` 从 0 到 1（`transform-origin: left center`）
- 加速度箭头可用不同颜色区分
- GSAP：`tl.fromTo("#velocity-arrow line", {scaleX: 0}, {scaleX: 1, duration: 0.7, ease: "power2.out"}, t)`

---

### 3. 自由落体 / 抛物运动

```svg
<g id="freefall">
  <!-- 小球 -->
  <circle id="ball" cx="50" cy="30" r="22" fill="var(--primary)"/>
  <!-- 高度标尺 -->
  <line x1="100" y1="10" x2="100" y2="200" stroke="var(--muted)" stroke-width="2"/>
  <text x="115" y="110" font-size="20" fill="var(--muted)">h</text>
  <!-- 重力箭头 -->
  <g transform="translate(30, 80)">
    <line x1="0" y1="0" x2="0" y2="60" stroke="var(--contrast)" stroke-width="4" marker-end="url(#gArrow)"/>
    <text x="10" y="35" font-size="18" fill="var(--contrast)">g</text>
  </g>
</g>
```

**动效建议**：
- 小球下落：y 方向移动，带加速感（`ease: "power2.in"`）
- 轨迹线：stroke-dashoffset 绘制

---

### 4. 弹簧振子

```svg
<g id="spring-system">
  <!-- 顶部固定 -->
  <rect x="40" y="0" width="120" height="15" fill="var(--muted)" rx="3"/>
  <!-- 弹簧（用 path 绘制锯齿） -->
  <path id="spring" d="M100,15 L85,30 L115,45 L85,60 L115,75 L85,90 L115,105 L100,120" 
        stroke="var(--accent)" stroke-width="4" fill="none" stroke-linecap="round"/>
  <!-- 重物 -->
  <circle id="mass" cx="100" cy="150" r="30" fill="var(--primary)"/>
  <text x="100" y="158" text-anchor="middle" font-size="20" fill="#fff" font-weight="700">m</text>
</g>
```

**动效建议**：
- 弹簧上下振动：y 方向 sin 运动
- 弹簧长度变化：path 形态变化（或直接整体缩放）

---

## 二、波动类组件

### 5. 正弦波形

```svg
<g id="sine-wave">
  <path id="wave" d="M0,100 Q25,60 50,100 T100,100 T150,100 T200,100 T250,100 T300,100 T350,100 T400,100"
        stroke="var(--primary)" stroke-width="4" fill="none" stroke-linecap="round"/>
  <!-- 波长标注 -->
  <line x1="0" y1="160" x2="100" y2="160" stroke="var(--muted)" stroke-width="2" stroke-dasharray="4,4"/>
  <text x="50" y="185" text-anchor="middle" font-size="20" fill="var(--muted)">λ</text>
  <!-- 振幅标注 -->
  <line x1="-20" y1="100" x2="-20" y2="60" stroke="var(--accent)" stroke-width="2"/>
  <text x="-35" y="85" text-anchor="middle" font-size="20" fill="var(--accent)">A</text>
</g>
```

**动效建议**：
- 描边入场：stroke-dashoffset 从总长到 0
- 波形流动：x 方向平移（需要 mask 裁切）
- 波长/振幅标注：延迟弹出

---

### 6. 纵波（疏密波）

```svg
<g id="longitudinal-wave">
  <!-- 多圈弹簧圈 -->
  <g id="compressions">
    <circle cx="30" cy="100" r="8" fill="var(--primary)"/>
    <circle cx="50" cy="100" r="8" fill="var(--primary)"/>
    <circle cx="65" cy="100" r="8" fill="var(--primary-deep)"/>
    <circle cx="80" cy="100" r="8" fill="var(--primary-deep)"/>
    <circle cx="100" cy="100" r="8" fill="var(--primary)"/>
    <circle cx="130" cy="100" r="8" fill="var(--primary)"/>
    <circle cx="160" cy="100" r="8" fill="var(--primary-deep)"/>
    <circle cx="175" cy="100" r="8" fill="var(--primary-deep)"/>
    <circle cx="200" cy="100" r="8" fill="var(--primary)"/>
    <circle cx="230" cy="100" r="8" fill="var(--primary)"/>
  </g>
</g>
```

**动效建议**：
- 疏密交替：各圆 x 方向交替运动
- 波传播：整体 stagger 移动

---

## 三、光学类组件

### 7. 三棱镜色散

```svg
<g id="prism">
  <!-- 三棱镜 -->
  <polygon points="200,50 150,150 250,150" fill="rgba(200,220,240,0.6)" stroke="var(--contrast)" stroke-width="2"/>
  <!-- 入射白光 -->
  <line x1="50" y1="100" x2="170" y2="100" stroke="#fff" stroke-width="4"/>
  <!-- 色散七色光 -->
  <line x1="230" y1="100" x2="350" y2="60" stroke="#E74C3C" stroke-width="2"/>
  <line x1="230" y1="100" x2="350" y2="75" stroke="#F39C12" stroke-width="2"/>
  <line x1="230" y1="100" x2="350" y2="90" stroke="#F1C40F" stroke-width="2"/>
  <line x1="230" y1="100" x2="350" y2="105" stroke="#2ECC71" stroke-width="2"/>
  <line x1="230" y1="100" x2="350" y2="120" stroke="#3498DB" stroke-width="2"/>
  <line x1="230" y1="100" x2="350" y2="135" stroke="#9B59B6" stroke-width="2"/>
</g>
```

**动效建议**：
- 白光先入射：scaleX 从 0 到 1
- 棱镜出现后，七色光依次射出（stagger）

---

### 8. 光路反射 / 折射

```svg
<g id="reflection">
  <!-- 界面 -->
  <line x1="0" y1="100" x2="400" y2="100" stroke="var(--muted)" stroke-width="2" stroke-dasharray="8,4"/>
  <!-- 法线 -->
  <line x1="200" y1="20" x2="200" y2="180" stroke="var(--muted)" stroke-width="1" stroke-dasharray="4,4"/>
  <text x="210" y="30" font-size="16" fill="var(--muted)">法线</text>
  <!-- 入射光线 -->
  <line id="incident" x1="80" y1="30" x2="200" y2="100" stroke="var(--primary)" stroke-width="3" marker-end="url(#arrowHead)"/>
  <!-- 反射光线 -->
  <line id="reflected" x1="200" y1="100" x2="320" y2="30" stroke="var(--accent)" stroke-width="3" marker-end="url(#arrowHead)"/>
  <!-- 入射角标注 -->
  <path d="M200,100 A50,50 0 0,1 165,60" fill="none" stroke="var(--primary)" stroke-width="2"/>
  <text x="155" y="75" font-size="18" fill="var(--primary)">θ₁</text>
</g>
```

**动效建议**：
- 入射光先绘制（从入射点向光源方向，或光源向入射点）
- 反射光延迟出现
- 角度标注最后弹出

---

## 四、化学 / 生物类组件

### 9. 原子结构

```svg
<g id="atom">
  <!-- 原子核 -->
  <circle cx="200" cy="150" r="25" fill="var(--primary-deep)"/>
  <text x="200" y="157" text-anchor="middle" font-size="16" fill="#fff" font-weight="700">+</text>
  <!-- 电子轨道 -->
  <ellipse cx="200" cy="150" rx="80" ry="40" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="4,3"/>
  <ellipse cx="200" cy="150" rx="60" ry="70" fill="none" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="4,3" transform="rotate(60 200 150)"/>
  <!-- 电子 -->
  <circle class="electron" cx="280" cy="150" r="10" fill="var(--contrast)"/>
  <circle class="electron" cx="200" cy="80" r="10" fill="var(--accent)"/>
</g>
```

**动效建议**：
- 原子核缩放出现
- 轨道依次绘制（stroke-dashoffset）
- 电子沿轨道旋转（可用 CSS animation 或 GSAP motionPath）

---

### 10. DNA 双螺旋（简化版）

```svg
<g id="dna">
  <!-- 左侧链 -->
  <path id="dna-left" d="M50,20 C80,50 20,80 50,110 C80,140 20,170 50,200 C80,230 20,260 50,290"
        stroke="var(--primary)" stroke-width="4" fill="none"/>
  <!-- 右侧链 -->
  <path id="dna-right" d="M150,20 C120,50 180,80 150,110 C120,140 180,170 150,200 C120,230 180,260 150,290"
        stroke="var(--contrast)" stroke-width="4" fill="none"/>
  <!-- 碱基对 -->
  <line x1="65" y1="45" x2="135" y2="45" stroke="var(--accent)" stroke-width="3"/>
  <line x1="65" y1="110" x2="135" y2="110" stroke="var(--accent)" stroke-width="3"/>
  <line x1="65" y1="175" x2="135" y2="175" stroke="var(--accent)" stroke-width="3"/>
  <line x1="65" y1="240" x2="135" y2="240" stroke="var(--accent)" stroke-width="3"/>
</g>
```

**动效建议**：
- 两条链从上到下依次绘制
- 碱基对 stagger 出现
- 整体可加缓慢旋转（3D 感可用 scaleX 波动模拟）

---

## 五、数学 / 通用组件

### 11. 坐标系

```svg
<g id="coordinate-system">
  <!-- X 轴 -->
  <line x1="50" y1="200" x2="450" y2="200" stroke="var(--ink-soft)" stroke-width="2" marker-end="url(#axisArrow)"/>
  <!-- Y 轴 -->
  <line x1="100" y1="350" x2="100" y2="50" stroke="var(--ink-soft)" stroke-width="2" marker-end="url(#axisArrow)"/>
  <!-- 原点 -->
  <text x="80" y="220" font-size="20" fill="var(--muted)">O</text>
  <!-- 轴标签 -->
  <text x="440" y="225" font-size="22" fill="var(--muted)">x</text>
  <text x="110" y="65" font-size="22" fill="var(--muted)">y</text>
  <!-- 网格 -->
  <g opacity="0.3">
    <line x1="100" y1="100" x2="400" y2="100" stroke="var(--line)" stroke-width="1"/>
    <line x1="100" y1="150" x2="400" y2="150" stroke="var(--line)" stroke-width="1"/>
    <line x1="100" y1="250" x2="400" y2="250" stroke="var(--line)" stroke-width="1"/>
    <line x1="100" y1="300" x2="400" y2="300" stroke="var(--line)" stroke-width="1"/>
    <line x1="200" y1="50" x2="200" y2="350" stroke="var(--line)" stroke-width="1"/>
    <line x1="300" y1="50" x2="300" y2="350" stroke="var(--line)" stroke-width="1"/>
    <line x1="400" y1="50" x2="400" y2="350" stroke="var(--line)" stroke-width="1"/>
  </g>
  <defs>
    <marker id="axisArrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
      <path d="M0,0 L10,4 L0,8 Z" fill="var(--ink-soft)"/>
    </marker>
  </defs>
</g>
```

**动效建议**：
- 坐标轴从原点向两端绘制
- 网格淡入
- 函数曲线后绘制（stroke-dashoffset）

---

### 12. 标注线（Callout Line）

```svg
<g id="callout-line">
  <!-- 从标注点指向说明文字的线 -->
  <line x1="100" y1="100" x2="200" y2="60" stroke="var(--primary)" stroke-width="2" stroke-dasharray="6,4"/>
  <circle cx="100" cy="100" r="5" fill="var(--primary)"/>
</g>
```

---

## 六、SVG 动效实现模式

### 模式 1：描边绘制（最常用）

```js
// 计算路径长度，设置 dasharray，动画 dashoffset
const len = el.getTotalLength();
el.style.strokeDasharray = len;
tl.fromTo(el, { strokeDashoffset: len },
  { strokeDashoffset: 0, duration: 0.8, ease: "power2.inOut" }, t);
```

### 模式 2：缩放入场

```js
// 从中心缩放出现
tl.fromTo(el, { scale: 0, transformOrigin: "center" },
  { scale: 1, duration: 0.5, ease: "back.out(1.5)" }, t);
```

### 模式 3：平移入场

```js
// 从左侧滑入
tl.fromTo(el, { x: -50, opacity: 0 },
  { x: 0, opacity: 1, duration: 0.6, ease: "power3.out" }, t);
```

### 模式 4：颜色渐变

```js
// 颜色从浅色变到主色
tl.fromTo(el, { fill: "var(--primary-soft)" },
  { fill: "var(--primary)", duration: 0.8, ease: "power2.out" }, t);
```

### 模式 5：部件 stagger

```js
// 多个元素按顺序出现
tl.fromTo(".parts", { opacity: 0, y: 20 },
  { opacity: 1, y: 0, duration: 0.4, ease: "power2.out", stagger: 0.12 }, t);
```
