#!/bin/bash
# 纳川 Skills 一键推送脚本
# 用法: ./push_to_github.sh
#
# 首次使用前，请先在 GitHub 上创建仓库：
#   1. 打开 https://github.com/new
#   2. Repository name 填: nachuan-stu
#   3. 选 Public（公开）
#   4. 不要勾选 "Initialize this repository with a README"
#   5. 点 Create repository
#
# 创建完后，运行本脚本即可推送。

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$(dirname "$SCRIPT_DIR")"

cd "$SKILLS_DIR"

echo "========================================"
echo "  纳川 Skills 一键推送"
echo "========================================"
echo ""

# 检查是否有未提交的变更
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "📝 检测到未提交的变更，正在提交..."
    git add -A
    git commit -m "update: $(date '+%Y-%m-%d %H:%M') 更新"
    echo "✅ 已提交"
else
    echo "📝 没有未提交的变更"
fi

echo ""
echo "🚀 正在推送到 GitHub..."

# 检查是否已设置远程
if git remote get-url origin > /dev/null 2>&1; then
    echo "   远程仓库: $(git remote get-url origin)"
else
    echo "   未设置远程仓库，正在添加..."
    git remote add origin https://github.com/wilsondd-lab/nachuan-stu.git
fi

# 推送
if git push -u origin main 2>&1; then
    echo ""
    echo "✅ 推送成功！"
    echo "📦 你的仓库地址: https://github.com/wilsondd-lab/nachuan-stu"
    echo ""
    echo "安装方法："
    echo "  npx skills add wilsondd-lab/nachuan-stu -s nachuan-tujie"
    echo "  npx skills add wilsondd-lab/nachuan-stu -s nachuan-teachingvideo"
else
    echo ""
    echo "❌ 推送失败"
    echo ""
    echo "可能的原因："
    echo "  1. GitHub 上还没有创建 nachuan-stu 仓库"
    echo "     → 去这里创建：https://github.com/new"
    echo "     → Repository name 填: nachuan-stu"
    echo "     → 选 Public"
    echo "     → 不要勾选 Initialize with README"
    echo ""
    echo "  2. 需要登录 GitHub 账号"
    echo "     → Mac 上可以用 GitHub Desktop 登录更方便"
    echo "     → 或运行: git config --global credential.helper osxkeychain"
    echo ""
    exit 1
fi
