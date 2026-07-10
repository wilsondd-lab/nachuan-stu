# 纳川图解 · SVG 组件库

> 可复用的 SVG 组件代码片段，AI 创作时直接复制粘贴，保证视觉统一和绘制精确。

---

## 一、箭头组件

箭头是物理/数学图示中最常用的元素。所有箭头使用 SVG `<marker>` 定义，可灵活复用。

### 1.1 基础箭头（marker 定义）

**必须放在 `<defs>` 中，定义一次可多次引用。**

```svg
<defs>
  <!-- 向右箭头 -->
  <marker id="arrowRight" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
    <path d="M0,0 L12,6 L0,12 z" fill="#6B8E9F"/>
  </marker>
  
  <!-- 向左箭头 -->
  <marker id="arrowLeft" markerWidth="12" markerHeight="12" refX="2" refY="6" orient="auto">
    <path d="M12,0 L0,6 L12,12 z" fill="#6B8E9F"/>
  </marker>
  
  <!-- 双向箭头 -->
  <marker id="arrowStart" markerWidth="12" markerHeight="12" refX="2" refY="6" orient="auto">
    <path d="M12,0 L0,6 L12,12 z" fill="#6B8E9F"/>
  </marker>
  <marker id="arrowEnd" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
    <path d="M0,0 L12,6 L0,12 z" fill="#6B8E9F"/>
  </marker>
</defs>
```

### 1.2 直线箭头

```svg
<!-- 水平箭头 -->
<line x1="50" y1="50" x2="200" y2="50" stroke="#6B8E9F" stroke-width="3" marker-end="url(#arrowRight)"/>

<!-- 垂直箭头 -->
<line x1="100" y1="20" x2="100" y2="150" stroke="#6B8E9F" stroke-width="3" marker-end="url(#arrowRight)"/>

<!-- 斜线箭头 -->
<line x1="50" y1="150" x2="200" y2="50" stroke="#6B8E9F" stroke-width="3" marker-end="url(#arrowRight)"/>

<!-- 双向箭头 -->
<line x1="50" y1="50" x2="200" y2="50" stroke="#6B8E9F" stroke-width="3"
      marker-start="url(#arrowStart)" marker-end="url(#arrowEnd)"/>
```

### 1.3 虚线箭头（辅助/变化量）

```svg
<line x1="50" y1="50" x2="200" y2="50" 
      stroke="#B87C7C" stroke-width="2.5" stroke-dasharray="6,4"
      marker-end="url(#arrowRight)"/>
```

### 1.4 曲线箭头（抛物/弯曲路径）

```svg
<!-- 二次贝塞尔曲线箭头 -->
<path d="M50,100 Q125,20 200,100" 
      fill="none" stroke="#6B8E9F" stroke-width="3"
      marker-end="url(#arrowRight)"/>

<!-- 三次贝塞尔曲线箭头 -->
<path d="M50,100 C80,20 170,20 200,100" 
      fill="none" stroke="#6B8E9F" stroke-width="3"
      marker-end="url(#arrowRight)"/>
```

### 1.5 带标注的箭头

```svg
<g>
  <line x1="50" y1="80" x2="250" y2="80" stroke="#6B8E9F" stroke-width="3" marker-end="url(#arrowRight)"/>
  <text x="150" y="65" text-anchor="middle" font-size="18" fill="#4A6B7A" font-weight="600">v = 10 m/s</text>
</g>
```

---

## 二、坐标系组件

### 2.1 直角坐标系（基础）

```svg
<svg viewBox="0 0 400 300" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="axisArrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#636E72"/>
    </marker>
  </defs>
  
  <!-- 网格（浅灰） -->
  <g stroke="#DFE6E9" stroke-width="1">
    <line x1="40" y1="20" x2="40" y2="260"/>
    <line x1="90" y1="20" x2="90" y2="260"/>
    <line x1="140" y1="20" x2="140" y2="260"/>
    <line x1="190" y1="20" x2="190" y2="260"/>
    <line x1="240" y1="20" x2="240" y2="260"/>
    <line x1="290" y1="20" x2="290" y2="260"/>
    <line x1="340" y1="20" x2="340" y2="260"/>
    <line x1="20" y1="40" x2="370" y2="40"/>
    <line x1="20" y1="90" x2="370" y2="90"/>
    <line x1="20" y1="140" x2="370" y2="140"/>
    <line x1="20" y1="190" x2="370" y2="190"/>
    <line x1="20" y1="240" x2="370" y2="240"/>
  </g>
  
  <!-- X轴 -->
  <line x1="30" y1="140" x2="370" y2="140" stroke="#636E72" stroke-width="2" marker-end="url(#axisArrow)"/>
  <text x="375" y="145" font-size="14" fill="#636E72">x</text>
  
  <!-- Y轴 -->
  <line x1="40" y1="250" x2="40" y2="20" stroke="#636E72" stroke-width="2" marker-end="url(#axisArrow)"/>
  <text x="35" y="18" text-anchor="end" font-size="14" fill="#636E72">y</text>
  
  <!-- 原点 -->
  <text x="30" y="155" font-size="14" fill="#636E72">O</text>
</svg>
```

### 2.2 带刻度的坐标系

```svg
<g>
  <!-- X轴刻度 -->
  <g font-size="12" fill="#636E72" text-anchor="middle">
    <line x1="90" y1="138" x2="90" y2="142" stroke="#636E72" stroke-width="1.5"/>
    <text x="90" y="158">1</text>
    <line x1="140" y1="138" x2="140" y2="142" stroke="#636E72" stroke-width="1.5"/>
    <text x="140" y="158">2</text>
    <line x1="190" y1="138" x2="190" y2="142" stroke="#636E72" stroke-width="1.5"/>
    <text x="190" y="158">3</text>
    <line x1="240" y1="138" x2="240" y2="142" stroke="#636E72" stroke-width="1.5"/>
    <text x="240" y="158">4</text>
    <line x1="290" y1="138" x2="290" y2="142" stroke="#636E72" stroke-width="1.5"/>
    <text x="290" y="158">5</text>
  </g>
  
  <!-- Y轴刻度 -->
  <g font-size="12" fill="#636E72" text-anchor="end">
    <line x1="38" y1="90" x2="42" y2="90" stroke="#636E72" stroke-width="1.5"/>
    <text x="32" y="94">1</text>
    <line x1="38" y1="40" x2="42" y2="40" stroke="#636E72" stroke-width="1.5"/>
    <text x="32" y="44">2</text>
  </g>
</g>
```

### 2.3 函数图像（直线）

```svg
<!-- y = kx + b 形式 -->
<line x1="40" y1="240" x2="360" y2="40" 
      stroke="#6B8E9F" stroke-width="3" 
      marker-end="url(#axisArrow)"/>

<!-- 标注斜率 -->
<text x="250" y="80" font-size="16" fill="#4A6B7A" font-weight="600">y = kx + b</text>
```

### 2.4 函数图像（曲线）

```svg
<!-- 抛物线 y = x²（开口向上） -->
<path d="M140,240 Q40,100 240,40 Q440,100 340,240" 
      fill="none" stroke="#C4A484" stroke-width="3"/>

<!-- 正弦曲线 -->
<path d="M40,140 Q90,40 140,140 T240,140 T340,140" 
      fill="none" stroke="#7C9B7C" stroke-width="3"/>
```

---

## 三、公式写法规范

### 3.1 用 HTML 写公式（推荐）

对于简单公式，直接用 HTML + CSS 书写，配合等宽字体。

```html
<div class="formula">
  <span class="var">v</span> = <span class="var">s</span> / <span class="var">t</span>
</div>
```

```css
.formula {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 36px;
  font-weight: 600;
  letter-spacing: 2px;
}
.formula .var {
  font-style: italic;
  color: var(--color-primary-dark);
}
```

### 3.2 上下标

```html
<!-- 下标 -->
v<sub>0</sub>    <!-- v₀ -->
a<sub>t</sub>    <!-- a_t -->

<!-- 上标 -->
x<sup>2</sup>    <!-- x² -->
m/s<sup>2</sup>  <!-- m/s² -->

<!-- 组合 -->
v<sub>t</sub><sup>2</sup>  <!-- v_t² -->
```

### 3.3 分数（SVG 精确绘制）

对于复杂分数，使用 SVG 绘制：

```svg
<svg width="120" height="80" viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <!-- 分子 -->
  <text x="60" y="28" text-anchor="middle" font-family="serif" font-size="28" font-style="italic" fill="#2D3436">Δv</text>
  <!-- 分数线 -->
  <line x1="10" y1="42" x2="110" y2="42" stroke="#2D3436" stroke-width="2"/>
  <!-- 分母 -->
  <text x="60" y="68" text-anchor="middle" font-family="serif" font-size="28" font-style="italic" fill="#2D3436">t</text>
</svg>
```

### 3.4 希腊字母

| 字母 | HTML 实体 | 用途示例 |
|------|-----------|----------|
| α | `&alpha;` | 角加速度 |
| β | `&beta;` | 角度 |
| γ | `&gamma;` | 伽马 |
| δ | `&delta;` | 变化量（小） |
| Δ | `&Delta;` | 变化量（大）如 Δv |
| θ | `&theta;` | 角度 |
| λ | `&lambda;` | 波长 |
| μ | `&mu;` | 摩擦系数 |
| π | `&pi;` | 圆周率 |
| ρ | `&rho;` | 密度 |
| σ | `&sigma;` | 电导率 |
| φ | `&phi;` | 相位 |
| ω | `&omega;` | 角速度 |
| Ω | `&Omega;` | 欧姆（电阻单位） |

### 3.5 数学符号

| 符号 | HTML 实体 | 说明 |
|------|-----------|------|
| ± | `&plusmn;` | 正负号 |
| × | `&times;` | 乘号 |
| ÷ | `&divide;` | 除号 |
| ≠ | `&ne;` | 不等于 |
| ≤ | `&le;` | 小于等于 |
| ≥ | `&ge;` | 大于等于 |
| ∞ | `&infin;` | 无穷大 |
| √ | `&radic;` | 根号 |
| ∝ | `&prop;` | 成正比 |
| ° | `&deg;` | 度 |
| ∑ | `&sum;` | 求和 |
| ∫ | `&int;` | 积分 |

---

## 四、卡片组件

### 4.1 基础卡片（HTML）

```html
<div class="card">
  <div class="card-title">标题</div>
  <div class="card-body">内容文字</div>
</div>
```

```css
.card {
  background: #FFFFFF;
  border-radius: 16px;
  padding: 24px 28px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.card-title {
  font-size: 28px;
  font-weight: 600;
  color: #2D3436;
  margin-bottom: 12px;
}
.card-body {
  font-size: 22px;
  color: #636E72;
  line-height: 1.5;
}
```

### 4.2 带左边框的强调卡片

```html
<div class="card card-accent">
  <!-- 内容 -->
</div>
```

```css
.card-accent {
  border-left: 6px solid var(--color-primary);
}
```

### 4.3 带顶部色条的卡片

```css
.card-topbar {
  border-top: 4px solid var(--color-primary);
}
```

### 4.4 渐变头部卡片

```html
<div class="gradient-card">
  <div class="gradient-header">
    <div class="card-number">1</div>
    <div>
      <div class="card-title">标题</div>
      <div class="card-subtitle">副标题</div>
    </div>
  </div>
  <div class="card-body">
    <!-- 内容 -->
  </div>
</div>
```

```css
.gradient-card {
  background: #FFFFFF;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(0,0,0,0.06);
}
.gradient-header {
  background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-dark) 100%);
  padding: 20px 28px;
  color: white;
  display: flex;
  align-items: center;
  gap: 16px;
}
.card-number {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(255,255,255,0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  font-weight: 700;
}
```

---

## 五、进度条组件

### 5.1 基础进度条

```html
<div class="progress-bar">
  <div class="progress-fill" style="width: 75%;"></div>
</div>
```

```css
.progress-bar {
  width: 100%;
  height: 12px;
  background: #DFE6E9;
  border-radius: 6px;
  overflow: hidden;
}
.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--color-primary-light), var(--color-primary));
  border-radius: 6px;
  transition: width 0.3s ease;
}
```

### 5.2 带标签的进度条

```html
<div class="progress-with-label">
  <div class="progress-label">
    <span>掌握程度</span>
    <span>75%</span>
  </div>
  <div class="progress-bar">
    <div class="progress-fill" style="width: 75%;"></div>
  </div>
</div>
```

```css
.progress-with-label .progress-label {
  display: flex;
  justify-content: space-between;
  font-size: 18px;
  color: #636E72;
  margin-bottom: 8px;
}
```

---

## 六、徽章/标签组件

### 6.1 基础徽章

```html
<span class="badge badge-primary">物理</span>
<span class="badge badge-success">重点</span>
<span class="badge badge-warning">易错</span>
<span class="badge badge-info">了解</span>
```

```css
.badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 14px;
  border-radius: 100px;
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 1px;
}
.badge-primary {
  background: var(--color-primary-bg);
  color: var(--color-primary-dark);
}
.badge-success {
  background: #E0EDE0;
  color: #5D7A5D;
}
.badge-warning {
  background: #F0E0E0;
  color: #9B5D5D;
}
.badge-info {
  background: #E0E8ED;
  color: #5D7A8C;
}
```

### 6.2 实心徽章

```css
.badge-solid {
  background: var(--color-primary);
  color: white;
}
```

### 6.3 带图标的徽章

```html
<span class="badge badge-icon">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
    <circle cx="12" cy="12" r="10"/>
    <path d="M12 16v-4M12 8h.01"/>
  </svg>
  注意
</span>
```

---

## 七、物理图示组件

### 7.1 受力分析图

```svg
<svg viewBox="0 0 300 250" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="forceArrow" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto">
      <path d="M0,0 L12,6 L0,12 z" fill="#B87C7C"/>
    </marker>
  </defs>
  
  <!-- 物体（方块） -->
  <rect x="120" y="100" width="60" height="60" rx="4" fill="#A8C0CC" stroke="#6B8E9F" stroke-width="2"/>
  <text x="150" y="138" text-anchor="middle" font-size="20" fill="#4A6B7A" font-weight="600">m</text>
  
  <!-- 重力 G（向下） -->
  <line x1="150" y1="160" x2="150" y2="220" stroke="#B87C7C" stroke-width="3" marker-end="url(#forceArrow)"/>
  <text x="160" y="200" font-size="18" fill="#B87C7C" font-weight="600">G</text>
  
  <!-- 支持力 N（向上） -->
  <line x1="150" y1="100" x2="150" y2="40" stroke="#7C9B7C" stroke-width="3" marker-end="url(#forceArrow)"/>
  <text x="160" y="60" font-size="18" fill="#7C9B7C" font-weight="600">N</text>
  
  <!-- 拉力 F（向右） -->
  <line x1="180" y1="130" x2="250" y2="130" stroke="#C4A484" stroke-width="3" marker-end="url(#forceArrow)"/>
  <text x="220" y="120" font-size="18" fill="#C4A484" font-weight="600">F</text>
  
  <!-- 摩擦力 f（向左） -->
  <line x1="120" y1="140" x2="60" y2="140" stroke="#636E72" stroke-width="3" marker-end="url(#forceArrow)"/>
  <text x="80" y="130" font-size="18" fill="#636E72" font-weight="600">f</text>
</svg>
```

### 7.2 斜面物体

```svg
<svg viewBox="0 0 300 250" xmlns="http://www.w3.org/2000/svg">
  <!-- 斜面 -->
  <path d="M30,200 L270,200 L270,80 Z" fill="#E8F0F3" stroke="#6B8E9F" stroke-width="2"/>
  
  <!-- 斜面上的方块 -->
  <g transform="translate(180, 110) rotate(-30)">
    <rect x="-25" y="-25" width="50" height="50" rx="4" fill="#C4A484" stroke="#A08060" stroke-width="2"/>
  </g>
  
  <!-- 角度标注 -->
  <path d="M60,200 A30,30 0 0,1 85.5,185" fill="none" stroke="#636E72" stroke-width="1.5"/>
  <text x="70" y="185" font-size="16" fill="#636E72">θ</text>
</svg>
```

### 7.3 电路图符号

```svg
<!-- 电池 -->
<g>
  <line x1="10" y1="20" x2="10" y2="40" stroke="#2D3436" stroke-width="3"/>
  <line x1="20" y1="15" x2="20" y2="45" stroke="#2D3436" stroke-width="1.5"/>
  <line x1="0" y1="30" x2="10" y2="30" stroke="#2D3436" stroke-width="2"/>
  <line x1="20" y1="30" x2="30" y2="30" stroke="#2D3436" stroke-width="2"/>
</g>

<!-- 电阻 -->
<g>
  <path d="M0,30 L10,30 L15,20 L25,40 L35,20 L45,40 L50,30 L60,30" 
        fill="none" stroke="#2D3436" stroke-width="2"/>
</g>

<!-- 灯泡 -->
<g>
  <circle cx="30" cy="30" r="15" fill="none" stroke="#2D3436" stroke-width="2"/>
  <line x1="19" y1="19" x2="41" y2="41" stroke="#2D3436" stroke-width="1.5"/>
  <line x1="41" y1="19" x2="19" y2="41" stroke="#2D3436" stroke-width="1.5"/>
  <line x1="0" y1="30" x2="15" y2="30" stroke="#2D3436" stroke-width="2"/>
  <line x1="45" y1="30" x2="60" y2="30" stroke="#2D3436" stroke-width="2"/>
</g>

<!-- 开关 -->
<g>
  <circle cx="10" cy="30" r="3" fill="#2D3436"/>
  <circle cx="40" cy="30" r="3" fill="#2D3436"/>
  <line x1="10" y1="30" x2="38" y2="15" stroke="#2D3436" stroke-width="2"/>
  <line x1="0" y1="30" x2="7" y2="30" stroke="#2D3436" stroke-width="2"/>
  <line x1="43" y1="30" x2="50" y2="30" stroke="#2D3436" stroke-width="2"/>
</g>

<!-- 电流表 A -->
<g>
  <circle cx="25" cy="25" r="20" fill="none" stroke="#2D3436" stroke-width="2"/>
  <text x="25" y="32" text-anchor="middle" font-size="18" fill="#2D3436">A</text>
</g>

<!-- 电压表 V -->
<g>
  <circle cx="25" cy="25" r="20" fill="none" stroke="#2D3436" stroke-width="2"/>
  <text x="25" y="32" text-anchor="middle" font-size="18" fill="#2D3436">V</text>
</g>
```

---

## 八、化学图示组件

### 8.1 原子结构示意图

```svg
<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <!-- 原子核 -->
  <circle cx="100" cy="100" r="20" fill="#C4A484"/>
  <text x="100" y="107" text-anchor="middle" font-size="16" fill="white" font-weight="bold">+11</text>
  
  <!-- 第一层电子轨道 -->
  <circle cx="100" cy="100" r="40" fill="none" stroke="#6B8E9F" stroke-width="1.5" stroke-dasharray="4,3"/>
  <!-- 第一层电子（2个） -->
  <circle cx="100" cy="60" r="6" fill="#6B8E9F"/>
  <circle cx="100" cy="140" r="6" fill="#6B8E9F"/>
  
  <!-- 第二层电子轨道 -->
  <circle cx="100" cy="100" r="65" fill="none" stroke="#7C9B7C" stroke-width="1.5" stroke-dasharray="4,3"/>
  <!-- 第二层电子（8个） -->
  <circle cx="165" cy="100" r="6" fill="#7C9B7C"/>
  <circle cx="35" cy="100" r="6" fill="#7C9B7C"/>
  <circle cx="100" cy="35" r="6" fill="#7C9B7C"/>
  <circle cx="100" cy="165" r="6" fill="#7C9B7C"/>
  <circle cx="146" cy="54" r="6" fill="#7C9B7C"/>
  <circle cx="54" cy="146" r="6" fill="#7C9B7C"/>
  <circle cx="146" cy="146" r="6" fill="#7C9B7C"/>
  <circle cx="54" cy="54" r="6" fill="#7C9B7C"/>
  
  <!-- 第三层电子轨道 -->
  <circle cx="100" cy="100" r="90" fill="none" stroke="#B87C7C" stroke-width="1.5" stroke-dasharray="4,3"/>
  <!-- 第三层电子（1个） -->
  <circle cx="190" cy="100" r="6" fill="#B87C7C"/>
</svg>
```

### 8.2 实验装置（试管+酒精灯）

```svg
<svg viewBox="0 0 200 250" xmlns="http://www.w3.org/2000/svg">
  <!-- 试管 -->
  <path d="M70,30 L70,150 Q70,180 100,180 Q130,180 130,150 L130,30" 
        fill="none" stroke="#636E72" stroke-width="2.5"/>
  <!-- 试管内液体 -->
  <path d="M72,100 Q100,95 128,100 L128,148 Q128,175 100,175 Q72,175 72,148 Z" 
        fill="#A8C0CC" opacity="0.6"/>
  <line x1="72" y1="100" x2="128" y2="100" stroke="#6B8E9F" stroke-width="2"/>
  
  <!-- 铁架台 -->
  <line x1="30" y1="20" x2="30" y2="230" stroke="#2D3436" stroke-width="3"/>
  <line x1="10" y1="230" x2="80" y2="230" stroke="#2D3436" stroke-width="3"/>
  <line x1="30" y1="50" x2="70" y2="50" stroke="#2D3436" stroke-width="2"/>
  
  <!-- 酒精灯 -->
  <g transform="translate(85, 195)">
    <!-- 灯体 -->
    <path d="M10,30 L10,15 Q10,5 30,5 Q50,5 50,15 L50,30 Z" 
          fill="#C4A484" stroke="#A08060" stroke-width="1.5"/>
    <!-- 灯芯 -->
    <rect x="27" y="-5" width="6" height="12" fill="#636E72"/>
    <!-- 火焰 -->
    <path d="M30,-10 Q20,5 25,15 Q30,20 35,15 Q40,5 30,-10Z" 
          fill="#B87C7C" opacity="0.8"/>
    <path d="M30,-5 Q25,3 28,12 Q30,16 32,12 Q35,3 30,-5Z" 
          fill="#F5EDE0"/>
  </g>
</svg>
```

---

## 九、生物图示组件

### 9.1 细胞结构（动物细胞）

```svg
<svg viewBox="0 0 250 250" xmlns="http://www.w3.org/2000/svg">
  <!-- 细胞膜 -->
  <ellipse cx="125" cy="125" rx="110" ry="100" 
           fill="#E6EDE6" stroke="#7C9B7C" stroke-width="2.5"/>
  
  <!-- 细胞核 -->
  <circle cx="125" cy="125" r="35" fill="#B8ADC8" stroke="#8B7E9B" stroke-width="2"/>
  <circle cx="115" cy="118" r="6" fill="#6B5D7A"/>
  <text x="155" y="115" font-size="16" fill="#6B5D7A" font-weight="600">细胞核</text>
  
  <!-- 线粒体 -->
  <g transform="translate(60, 80)">
    <ellipse cx="0" cy="0" rx="20" ry="10" fill="none" stroke="#C4A484" stroke-width="2"/>
    <path d="M-15,0 Q-10,-5 -5,0 T5,0 T15,0" fill="none" stroke="#C4A484" stroke-width="1.5"/>
  </g>
  <text x="35" y="65" font-size="14" fill="#A08060">线粒体</text>
</svg>
```

---

## 十、使用原则

1. **所有图形用 SVG 绘制** — 保证矢量清晰、缩放不失真
2. **坐标可计算** — 物理/数学图形的坐标、比例必须准确
3. **颜色统一** — 使用设计系统中定义的颜色变量
4. **文字清晰** — SVG 中的文字使用系统字体，字号不小于 14px
5. **marker 复用** — 箭头通过 `<defs>` + `<marker>` 定义，不重复画箭头
6. **viewBox 设置** — 每个 SVG 都设置 viewBox，确保响应式缩放
7. **命名空间** — SVG 必须声明 `xmlns="http://www.w3.org/2000/svg"`
