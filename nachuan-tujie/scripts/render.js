#!/usr/bin/env node
/**
 * 纳川图解 · HTML模板渲染器
 *
 * 功能：
 *   1. 读取模板 HTML 文件
 *   2. 用 JSON 数据填充模板插槽（Mustache 风格）
 *   3. 通过 HyperFrames (Puppeteer) 渲染成 PNG
 *
 * 用法：
 *   node render.js --template concept --data data.json --output out.png
 *   node render.js --template compare --data data.json --output out.png --palette teal
 *
 * 模板类型：
 *   concept   - 概念卡（单概念多要点）
 *   compare   - 对比卡（左右对比）
 *   formula   - 公式卡（公式+变量+条件）
 *   steps     - 步骤卡（流程步骤）
 *   timeline  - 时间线（事件时间线）
 *   mindmap   - 思维导图（知识体系）
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync, spawn } = require('child_process');

// ============================================================
// 配置
// ============================================================

const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');
const DEFAULT_OUTPUT_DIR = path.join(process.cwd(), 'output');
const VIEWPORT_WIDTH = 1080;
const VIEWPORT_HEIGHT = 1920;
const DEVICE_SCALE_FACTOR = 2;

const TEMPLATE_MAP = {
  concept:  'template-concept.html',
  compare:  'template-compare.html',
  formula:  'template-formula.html',
  steps:    'template-steps.html',
  timeline: 'template-timeline.html',
  mindmap:  'template-mindmap.html',
};

// ============================================================
// 参数解析
// ============================================================

function parseArgs() {
  const args = process.argv.slice(2);
  const result = {
    template: null,
    data: null,
    output: null,
    htmlOutput: null,
    palette: null,
    help: false,
  };

  for (let i = 0; i < args.length; i++) {
    switch (args[i]) {
      case '--template':
      case '-t':
        result.template = args[++i];
        break;
      case '--data':
      case '-d':
        result.data = args[++i];
        break;
      case '--output':
      case '-o':
        result.output = args[++i];
        break;
      case '--html-output':
        result.htmlOutput = args[++i];
        break;
      case '--palette':
      case '-p':
        result.palette = args[++i];
        break;
      case '--help':
      case '-h':
        result.help = true;
        break;
    }
  }

  return result;
}

function printHelp() {
  console.log(`
纳川图解 · HTML模板渲染器
=========================

用法:
  node render.js --template <模板名> --data <JSON文件> [选项]

模板名:
  concept   概念卡（单概念多要点）
  compare   对比卡（左右对比）
  formula   公式卡（公式+变量+条件）
  steps     步骤卡（流程步骤）
  timeline  时间线（事件时间线）
  mindmap   思维导图（知识体系）

选项:
  --template, -t     模板名称（必填）
  --data, -d         JSON 数据文件路径（必填）
  --output, -o       输出 PNG 路径（默认 output/output.png）
  --html-output      输出 HTML 路径（默认同目录同名 .html）
  --palette, -p      主题色覆盖（默认从 data 中读取）
  --help, -h         显示帮助

示例:
  node render.js --template compare --data sample.json --output result.png
  node render.js --template formula --data data.json --palette purple
`);
}

// ============================================================
// 环境检测
// ============================================================

function checkNodeVersion() {
  const version = process.versions.node;
  const major = parseInt(version.split('.')[0], 10);
  if (major < 16) {
    console.error(`✗ Node.js 版本过低: v${version}`);
    console.error('  需要 Node.js v16 或更高版本');
    console.error('  请前往 https://nodejs.org 升级');
    process.exit(1);
  }
  return version;
}

function checkHyperFrames() {
  try {
    const result = execSync('npx hyperframes --version', {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 30000,
    }).trim();
    return result;
  } catch (e) {
    // 首次运行 npx 会自动安装，这里给一个友好提示
    return null;
  }
}

// ============================================================
// 简易 Mustache 模板引擎
// 支持:
//   {{变量}}     - 变量替换（HTML转义）
//   {{{变量}}}   - 变量替换（不转义，用于HTML内容）
//   {{.}}       - 当前元素（数组元素为基本类型时使用）
//   {{#列表}}...{{/列表}}   - 列表/对象/布尔 区块
// ============================================================

function renderTemplate(template, data) {
  let result = template;

  // 处理三段花括号（不转义 HTML）
  result = result.replace(/\{\{\{\s*([\w.]+)\s*\}\}\}/g, (match, key) => {
    const value = key === '.' ? data['.'] : getNestedValue(data, key);
    return value !== undefined && value !== null ? String(value) : '';
  });

  // 处理区块（列表 + 布尔）
  result = renderSections(result, data);

  // 处理普通变量（支持 {{.}} 表示当前元素）
  result = result.replace(/\{\{\s*([\w.]+)\s*\}\}/g, (match, key) => {
    if (key.startsWith('#') || key.startsWith('/') || key.startsWith('^')) {
      return match; // 区块标签在上面处理过了，这里跳过
    }
    const value = key === '.' ? data['.'] : getNestedValue(data, key);
    return value !== undefined && value !== null ? escapeHtml(String(value)) : '';
  });

  return result;
}

function renderSections(template, data) {
  const sectionRegex = /\{\{\#\s*(\w+)\s*\}\}([\s\S]*?)\{\{\/\s*\1\s*\}\}/g;
  let result = template;
  let match;

  // 循环处理，支持嵌套
  while ((match = sectionRegex.exec(result)) !== null) {
    const [fullMatch, sectionName, innerTemplate] = match;
    const value = getNestedValue(data, sectionName);

    let replacement = '';

    if (Array.isArray(value)) {
      // 列表渲染
      replacement = value.map(item => {
        // 如果 item 是基本类型（字符串/数字），用 '.' 表示当前元素
        const ctx = typeof item === 'object' && item !== null
          ? { ...data, ...item }
          : { ...data, '.': item };
        return renderTemplate(innerTemplate, ctx);
      }).join('');
    } else if (value && typeof value === 'object') {
      // 对象上下文
      replacement = renderTemplate(innerTemplate, { ...data, ...value });
    } else if (value) {
      // 真值
      replacement = renderTemplate(innerTemplate, data);
    }
    // 假值或空数组 → 不渲染

    result = result.slice(0, match.index) + replacement + result.slice(match.index + fullMatch.length);
    sectionRegex.lastIndex = match.index; // 重置索引，处理嵌套
  }

  return result;
}

function getNestedValue(data, key) {
  if (key in data) return data[key];
  // 支持点号路径（如 user.name）
  const parts = key.split('.');
  let current = data;
  for (const part of parts) {
    if (current == null || !(part in current)) return undefined;
    current = current[part];
  }
  return current;
}

function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// ============================================================
// 主题色处理
// ============================================================

const PALETTE_CLASS_MAP = {
  terracotta: 'palette-terracotta',
  slate: 'palette-slate',
  teal: 'palette-teal',
  purple: 'palette-purple',
  sage: 'palette-sage',
  caramel: 'palette-caramel',
  'sage-light': 'palette-sage-light',
  'default': 'palette-terracotta',
};

// 学科到默认配色的映射
const SUBJECT_PALETTE_MAP = {
  '物理': 'terracotta',
  '化学': 'teal',
  '数学': 'purple',
  '生物': 'sage',
  '语文': 'caramel',
  '历史': 'caramel',
  '英语': 'slate',
  '政治': 'slate',
  '地理': 'sage-light',
};

function resolvePalette(data, overridePalette) {
  if (overridePalette && PALETTE_CLASS_MAP[overridePalette]) {
    return PALETTE_CLASS_MAP[overridePalette];
  }
  if (data.palette && PALETTE_CLASS_MAP[data.palette]) {
    return PALETTE_CLASS_MAP[data.palette];
  }
  if (data.subject && SUBJECT_PALETTE_MAP[data.subject]) {
    return PALETTE_CLASS_MAP[SUBJECT_PALETTE_MAP[data.subject]];
  }
  return PALETTE_CLASS_MAP['default'];
}

function applyPaletteClass(html, paletteClass) {
  // 替换 body 的 class
  return html.replace(/<body\s+class="[^"]*"/, `<body class="${paletteClass}"`);
}

// ============================================================
// 主流程
// ============================================================

function main() {
  const args = parseArgs();

  if (args.help) {
    printHelp();
    process.exit(0);
  }

  // 校验必填参数
  if (!args.template) {
    console.error('✗ 缺少 --template 参数');
    console.error('  可选模板: ' + Object.keys(TEMPLATE_MAP).join(', '));
    process.exit(1);
  }

  if (!args.data) {
    console.error('✗ 缺少 --data 参数（JSON 数据文件路径）');
    process.exit(1);
  }

  if (!TEMPLATE_MAP[args.template]) {
    console.error(`✗ 未知模板: ${args.template}`);
    console.error('  可选模板: ' + Object.keys(TEMPLATE_MAP).join(', '));
    process.exit(1);
  }

  // 1. 检测 Node.js 版本
  const nodeVersion = checkNodeVersion();
  console.log(`✓ Node.js v${nodeVersion}`);

  // 2. 读取模板
  const templatePath = path.join(TEMPLATES_DIR, TEMPLATE_MAP[args.template]);
  if (!fs.existsSync(templatePath)) {
    console.error(`✗ 模板文件不存在: ${templatePath}`);
    process.exit(1);
  }
  const template = fs.readFileSync(templatePath, 'utf8');
  console.log(`✓ 加载模板: ${TEMPLATE_MAP[args.template]}`);

  // 3. 读取数据
  const dataPath = path.resolve(args.data);
  if (!fs.existsSync(dataPath)) {
    console.error(`✗ 数据文件不存在: ${dataPath}`);
    process.exit(1);
  }
  let data;
  try {
    data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
  } catch (e) {
    console.error(`✗ JSON 解析失败: ${e.message}`);
    process.exit(1);
  }
  console.log(`✓ 加载数据: ${path.basename(dataPath)}`);

  // 4. 渲染模板
  let html = renderTemplate(template, data);

  // 5. 应用主题色
  const paletteClass = resolvePalette(data, args.palette);
  html = applyPaletteClass(html, paletteClass);
  console.log(`✓ 主题色: ${paletteClass.replace('palette-', '')}`);

  // 6. 确定输出路径
  const outputPath = path.resolve(args.output || path.join(DEFAULT_OUTPUT_DIR, 'output.png'));
  const outputDir = path.dirname(outputPath);
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }

  // 7. 保存 HTML
  const htmlOutputPath = args.htmlOutput
    ? path.resolve(args.htmlOutput)
    : path.join(outputDir, path.basename(outputPath, '.png') + '.html');
  fs.writeFileSync(htmlOutputPath, html, 'utf8');
  console.log(`✓ HTML 已保存: ${htmlOutputPath}`);

  // 8. 检测 HyperFrames
  console.log('\n→ 检测 HyperFrames...');
  const hfVersion = checkHyperFrames();
  if (hfVersion) {
    console.log(`✓ HyperFrames ${hfVersion}`);
  } else {
    console.log('  首次运行，HyperFrames 将自动下载安装...');
  }

  // 9. 渲染 PNG
  console.log('\n→ 渲染 PNG...');
  try {
    const result = execSync(
      `npx hyperframes snapshot ` +
      `--input "${htmlOutputPath}" ` +
      `--output "${outputPath}" ` +
      `--width ${VIEWPORT_WIDTH} ` +
      `--height ${VIEWPORT_HEIGHT} ` +
      `--device-scale-factor ${DEVICE_SCALE_FACTOR} ` +
      `--wait 500`,
      {
        encoding: 'utf8',
        stdio: ['pipe', 'pipe', 'pipe'],
        timeout: 120000,
      }
    );
    console.log(result.trim());
  } catch (e) {
    // 如果 HyperFrames 不可用，给出清晰的错误提示
    console.error('\n✗ 渲染失败');
    if (e.stderr && e.stderr.includes('command not found')) {
      console.error('  HyperFrames 未安装或不可用。');
      console.error('  请确保已安装 Node.js 并能访问 npx。');
      console.error('  尝试手动安装: npm install -g hyperframes');
    } else if (e.stderr) {
      console.error('  ' + e.stderr.trim().split('\n').slice(0, 5).join('\n  '));
    } else {
      console.error('  ' + e.message);
    }
    console.error('\n  HTML 文件已生成，可以手动用浏览器打开查看:');
    console.error(`  ${htmlOutputPath}`);
    process.exit(1);
  }

  // 10. 完成
  const stats = fs.statSync(outputPath);
  console.log('\n' + '='.repeat(60));
  console.log('✓ 渲染完成！');
  console.log(`  🖼️  PNG:  ${outputPath} (${Math.round(stats.size / 1024)} KB)`);
  console.log(`  📄  HTML: ${htmlOutputPath}`);
  console.log(`  📐  尺寸: ${VIEWPORT_WIDTH}x${VIEWPORT_HEIGHT} @ ${DEVICE_SCALE_FACTOR}x`);
  console.log('='.repeat(60));
}

// 启动
main();
