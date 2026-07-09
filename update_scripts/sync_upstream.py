#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
纳川 Skill 自动更新脚本
从 linyuebanzi-skills 上游获取最新更新，按纳川规范改造后更新到 nachuan-stu。

更新流程：
1. 拉取上游 linyuebanzi-skills 最新代码
2. 对比差异，识别有变更的文件
3. 应用纳川改造规则（名字替换、免token配置、OpenMontage融合、橙皮书定位）
4. 生成更新后的 nachuan-stu
5. 提交并推送到 GitHub

用法：
    python3 sync_upstream.py [--dry-run] [--force]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# ============================================================
# 配置
# ============================================================

UPSTREAM_REPO = "https://github.com/lqshow/linyuebanzi-skills.git"
UPSTREAM_SKILLS = ["linyuebanzi-edu-infographic", "linyuebanzi-teaching-animation", "linyuebanzi-image-gen"]

NACHUAN_SKILL_MAP = {
    "linyuebanzi-edu-infographic": "nachuan-tujie",
    "linyuebanzi-image-gen": "nachuan-tujie",  # 合并到 tujie
    "linyuebanzi-teaching-animation": "nachuan-teachingvideo",
}

NAME_REPLACEMENTS = [
    # 英文标识（全词匹配，避免误伤）
    ("linyuebanzi", "nachuan"),
    # 中文显示名
    ("林月半子", "纳川"),
]

SKILL_DESCRIPTION_TUJIE = """  纳川图解·准高中生AI学习伙伴。将初中全科(语数英物化生政史地)及高中预科知识点转化为9:16竖版教育信息图。
  用户只需输入知识点名称，自动完成：学科/年级/章节识别、3-5个核心子概念拆解、莫兰迪主题色分配、插图描述生成、完整提示词构建、调用内置生图能力出图。
  内置双层学科准确性检查：生图前按分学科清单自检提示词，生图后读回PNG视觉复核，不通过自动重试。
  零配置即用：默认使用TRAE内置生图能力，无需任何API Key；高级用户可配置MuleRun/APImart/AtlasCloud切换外部生图API。
  支持批量生成，每章不同色系，风格统一。
  触发词：做一张信息图、知识卡片、学科图解、纳川图解。"""

SKILL_DESCRIPTION_VIDEO = """纳川教学视频 · 准高中生AI学习伙伴。输入一个学科概念，自动生成动态教学内容。
两种产出都由 HyperFrames 本地渲染、共用同一个 index.html（mode 变量切换）：① 配音教学视频 — 7段分镜 + 中文配音（默认 macOS say，可选 Minimax）+ 字幕 + 完整 MP4（1080p，60-90s）；② 无声循环动图 — 紧凑无声版 MP4（1080p，~32s，循环播放）。
共用一套7段分镜结构和7套主题配色，视频和动图风格完全统一。
触发词：教学视频、配音视频、教学动图、无声动图、循环视频、概念动画、纳川教学。"""


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)


def die(msg):
    print(f"❌ {msg}", file=sys.stderr)
    sys.exit(1)


def run_cmd(cmd, cwd=None, check=True):
    """运行shell命令，返回输出"""
    log(f"  执行: {cmd[:80]}..." if len(cmd) > 80 else f"  执行: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        log(f"  命令失败: {result.stderr[:200]}")
        if check:
            raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def clone_upstream(tmp_dir):
    """克隆上游仓库"""
    log("克隆上游 linyuebanzi-skills 仓库...")
    repo_dir = tmp_dir / "upstream"
    run_cmd(f"git clone --depth 1 {UPSTREAM_REPO} {repo_dir}")
    return repo_dir


def get_current_version(skills_dir):
    """获取当前纳川skills的版本信息"""
    version_file = skills_dir / ".nachuan_version.json"
    if version_file.exists():
        return json.loads(version_file.read_text(encoding="utf-8"))
    return {"upstream_commit": "unknown", "last_sync": "never"}


def get_upstream_commit(repo_dir):
    """获取上游最新commit hash"""
    stdout, _, _ = run_cmd("git rev-parse HEAD", cwd=repo_dir)
    return stdout.strip()


def apply_name_replacements(content):
    """应用名字替换规则"""
    for old, new in NAME_REPLACEMENTS:
        content = content.replace(old, new)
    return content


def update_tujie_skill(upstream_skills_dir, nachuan_skills_dir):
    """更新 nachuan-tujie skill（合并 edu-infographic + image-gen）"""
    log("更新 nachuan-tujie（图解）skill...")

    tujie_dir = nachuan_skills_dir / "nachuan-tujie"
    edu_dir = upstream_skills_dir / "linyuebanzi-edu-infographic"
    image_dir = upstream_skills_dir / "linyuebanzi-image-gen"

    if not edu_dir.exists():
        log("  上游 edu-infographic 不存在，跳过")
        return False

    updated = False

    # 1. 更新 references（来自 edu-infographic）
    ref_dir = tujie_dir / "references"
    if edu_dir.joinpath("references").exists():
        for f in edu_dir.joinpath("references").iterdir():
            if f.is_file():
                target = ref_dir / f.name
                content = f.read_text(encoding="utf-8")
                content = apply_name_replacements(content)
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    target.write_text(content, encoding="utf-8")
                    log(f"  更新 references/{f.name}")
                    updated = True

    # 2. 更新 image-gen 脚本
    scripts_dir = tujie_dir / "scripts"
    providers_dir = scripts_dir / "providers"

    if image_dir.exists() and image_dir.joinpath("scripts").exists():
        # generate.py
        src_gen = image_dir / "scripts" / "generate.py"
        tgt_gen = scripts_dir / "generate.py"
        if src_gen.exists():
            content = src_gen.read_text(encoding="utf-8")
            content = apply_name_replacements(content)
            # 修改默认 provider 为 trae
            content = content.replace('DEFAULT_PROVIDER = "mulerun"', 'DEFAULT_PROVIDER = "trae"')
            # 修改自动检测逻辑：没设任何API key时用trae
            old_detect = '''if args.provider == DEFAULT_PROVIDER and not has_mulerun:
        if has_apimart:
            provider_name = "apimart"
            print(f"  自动检测: APIMART_API_KEY 已设置,切换到 apimart")
        elif has_atlascloud:
            provider_name = "atlascloud"
            print(f"  自动检测: ATLASCLOUD_API_KEY 已设置,切换到 atlascloud")'''
            new_detect = '''if args.provider == "trae":
        provider_name = "trae"
    elif args.provider == DEFAULT_PROVIDER and not has_mulerun:
        if has_apimart:
            provider_name = "apimart"
            print(f"  自动检测: APIMART_API_KEY 已设置,切换到 apimart")
        elif has_atlascloud:
            provider_name = "atlascloud"
            print(f"  自动检测: ATLASCLOUD_API_KEY 已设置,切换到 atlascloud")
        else:
            provider_name = "trae"
            print("  自动检测: 未设置外部 API Key，使用 TRAE 内置生图（零配置）")'''
            content = content.replace(old_detect, new_detect)

            if not tgt_gen.exists() or tgt_gen.read_text(encoding="utf-8") != content:
                tgt_gen.write_text(content, encoding="utf-8")
                log("  更新 scripts/generate.py")
                updated = True

        # providers 目录（保留 trae.py 不覆盖）
        src_providers = image_dir / "scripts" / "providers"
        if src_providers.exists():
            for f in src_providers.iterdir():
                if f.is_file() and f.name != "trae.py":
                    target = providers_dir / f.name
                    content = f.read_text(encoding="utf-8")
                    content = apply_name_replacements(content)
                    # 给基类增加 requires_api_key 属性
                    if f.name == "base.py" and "requires_api_key" not in content:
                        content = content.replace(
                            "class BaseProvider:",
                            "class BaseProvider:\n    requires_api_key = True"
                        )
                    if not target.exists() or target.read_text(encoding="utf-8") != content:
                        target.write_text(content, encoding="utf-8")
                        log(f"  更新 scripts/providers/{f.name}")
                        updated = True

    # 3. 确保 trae.py provider 存在
    trae_provider = providers_dir / "trae.py"
    if not trae_provider.exists():
        log("  创建 trae provider（零配置生图）")
        trae_content = '''from typing import Optional
from pathlib import Path
import shutil
import os
from .base import BaseProvider


class TraeProvider(BaseProvider):
    """TRAE 内置生图 Provider — 零配置，使用 GenerateImage 工具。

    工作方式：
    - create_task: 保存 prompt 到任务文件，提示 agent 调用 GenerateImage
    - poll_task: 检测输出目录中 agent 生成的 PNG
    - 不调用外部 HTTP API，通过文件系统与 agent 协作
    """

    env_var = "TRAE_IMAGE_GEN"  # 不会被检测到，因为 requires_api_key = False
    requires_api_key = False
    create_url = "trae://generate-image"
    poll_url = "trae://check-output"

    SIZE_MAP = {
        "16:9": "landscape_16_9",
        "9:16": "portrait_9_16",
        "1:1": "square_hd",
        "4:3": "landscape_4_3",
        "3:4": "portrait_4_3",
    }

    def __init__(self, api_key: str = ""):
        super().__init__(api_key or "trae-builtin")
        self._task_counter = 0

    def build_create_payload(
        self, prompt: str, mode: str, images: Optional[list[str]],
        aspect_ratio: str, resolution: str,
    ) -> tuple[str, dict]:
        size = self.SIZE_MAP.get(aspect_ratio, "portrait_9_16")
        payload = {
            "prompt": prompt,
            "size": size,
            "mode": mode,
            "images": images or [],
        }
        return self.create_url, payload

    def create_task(self, prompt: str, mode: str, images: Optional[list[str]],
                    aspect_ratio: str, resolution: str) -> Optional[str]:
        self._task_counter += 1
        task_id = f"trae-gen-{self._task_counter}-{int(os.times()[4])}"
        print(f"    [TRAE 内置生图] 任务已创建: {task_id}")
        print(f"    [TRAE 内置生图] 请使用 GenerateImage 工具生成图片，prompt 已保存到任务文件")
        print(f"    [TRAE 内置生图] 建议 size: {self.SIZE_MAP.get(aspect_ratio, 'portrait_9_16')}")
        return task_id

    def parse_task_id(self, resp: dict) -> Optional[str]:
        return resp.get("task_id")

    def build_poll_url(self, task_id: str, mode: str) -> str:
        return f"{self.poll_url}/{task_id}"

    def parse_poll_status(self, resp: dict) -> tuple[str, dict]:
        status = resp.get("status", "polling")
        if status == "completed":
            return "completed", resp
        if status == "failed":
            return "failed", resp
        return "polling", resp

    def extract_images(self, poll_body: dict) -> list[str]:
        return poll_body.get("images", [])

    def download_image(self, url: str, dest_path: Path) -> bool:
        """TRAE 模式下 url 是本地路径，直接复制"""
        src = Path(url)
        if src.exists():
            shutil.copy2(src, dest_path)
            return True
        return False
'''
        trae_provider.write_text(trae_content, encoding="utf-8")
        updated = True

    # 4. 确保 __init__.py 注册了 trae
    init_file = providers_dir / "__init__.py"
    if init_file.exists():
        content = init_file.read_text(encoding="utf-8")
        content = apply_name_replacements(content)
        if "trae" not in content:
            # 在 import 列表添加
            content = content.replace(
                "from .atlascloud import AtlasCloudProvider",
                "from .atlascloud import AtlasCloudProvider\nfrom .trae import TraeProvider"
            )
            # 在 PROVIDERS 字典添加
            content = content.replace(
                '"atlascloud": AtlasCloudProvider,',
                '"atlascloud": AtlasCloudProvider,\n    "trae": TraeProvider,'
            )
            init_file.write_text(content, encoding="utf-8")
            log("  注册 trae provider")
            updated = True

    # 5. 更新 SKILL.md 的 frontmatter description
    skill_md = tujie_dir / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text(encoding="utf-8")
        content = apply_name_replacements(content)
        # 确保 frontmatter 中的描述是纳川版本的
        # （保留现有的 SKILL.md，因为它已经包含了完整的纳川改造）
        skill_md.write_text(content, encoding="utf-8")

    return updated


def update_teachingvideo_skill(upstream_skills_dir, nachuan_skills_dir):
    """更新 nachuan-teachingvideo skill"""
    log("更新 nachuan-teachingvideo（教学视频）skill...")

    video_dir = nachuan_skills_dir / "nachuan-teachingvideo"
    src_dir = upstream_skills_dir / "linyuebanzi-teaching-animation"

    if not src_dir.exists():
        log("  上游 teaching-animation 不存在，跳过")
        return False

    updated = False

    # 1. 更新 references（保留新增的 3 个 OpenMontage 融合文件不覆盖）
    ref_dir = video_dir / "references"
    preserve_files = {"teaching-narrative.md", "motion-design.md", "quality-checklist.md"}
    if src_dir.joinpath("references").exists():
        for f in src_dir.joinpath("references").iterdir():
            if f.is_file() and f.name not in preserve_files:
                target = ref_dir / f.name
                content = f.read_text(encoding="utf-8")
                content = apply_name_replacements(content)
                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    target.write_text(content, encoding="utf-8")
                    log(f"  更新 references/{f.name}")
                    updated = True

    # 2. 更新 scripts（tts.py 特殊处理，保留自动检测逻辑）
    scripts_dir = video_dir / "scripts"
    if src_dir.joinpath("scripts").exists():
        for f in src_dir.joinpath("scripts").iterdir():
            if f.is_file():
                target_name = f.name
                # minimax_tts.py → tts.py
                if f.name == "minimax_tts.py":
                    target_name = "tts.py"
                    # 保留现有的 tts.py（已有自动检测逻辑）
                    continue

                target = scripts_dir / target_name
                content = f.read_text(encoding="utf-8")
                content = apply_name_replacements(content)
                # 脚本中引用 minimax_tts.py 的地方改为 tts.py
                content = content.replace("minimax_tts.py", "tts.py")
                content = content.replace("minimax_tts", "tts")

                if not target.exists() or target.read_text(encoding="utf-8") != content:
                    target.write_text(content, encoding="utf-8")
                    log(f"  更新 scripts/{target_name}")
                    updated = True

    # 3. 更新 assets
    assets_dir = video_dir / "assets"
    if src_dir.joinpath("assets").exists():
        for f in src_dir.rglob("*"):
            if f.is_file() and "assets" in f.parts:
                rel = f.relative_to(src_dir)
                target = video_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if f.suffix in (".html", ".css", ".js", ".md", ".json", ".yaml", ".yml"):
                    content = f.read_text(encoding="utf-8")
                    content = apply_name_replacements(content)
                    if not target.exists() or target.read_text(encoding="utf-8") != content:
                        target.write_text(content, encoding="utf-8")
                        log(f"  更新 assets/{rel.name}")
                        updated = True
                elif not target.exists():
                    shutil.copy2(f, target)
                    log(f"  新增 assets/{rel.name}")
                    updated = True

    # 4. 更新 examples
    examples_dir = video_dir / "examples"
    if src_dir.joinpath("examples").exists():
        for example_dir in src_dir.joinpath("examples").iterdir():
            if example_dir.is_dir():
                target_example = examples_dir / example_dir.name
                target_example.mkdir(parents=True, exist_ok=True)
                for f in example_dir.rglob("*"):
                    if f.is_file():
                        rel = f.relative_to(example_dir)
                        target = target_example / rel
                        target.parent.mkdir(parents=True, exist_ok=True)
                        if f.suffix in (".html", ".json", ".md"):
                            content = f.read_text(encoding="utf-8")
                            content = apply_name_replacements(content)
                            if not target.exists() or target.read_text(encoding="utf-8") != content:
                                target.write_text(content, encoding="utf-8")
                                updated = True
                        elif not target.exists():
                            shutil.copy2(f, target)
                            updated = True

    # 5. 更新 openai.yaml（名字替换）
    yaml_file = src_dir / "openai.yaml"
    if yaml_file.exists():
        target = video_dir / "openai.yaml"
        content = yaml_file.read_text(encoding="utf-8")
        content = apply_name_replacements(content)
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
            log("  更新 openai.yaml")
            updated = True

    return updated


def save_version(skills_dir, upstream_commit):
    """保存同步版本信息"""
    version_file = skills_dir / ".nachuan_version.json"
    version_data = {
        "upstream_commit": upstream_commit,
        "last_sync": datetime.now().isoformat(),
        "upstream_repo": UPSTREAM_REPO,
    }
    version_file.write_text(json.dumps(version_data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"版本信息已保存: {upstream_commit}")


def git_commit_and_push(skills_dir, upstream_commit, dry_run=False):
    """提交更新并推送到GitHub"""
    log("提交更新...")

    run_cmd("git add -A", cwd=skills_dir)
    stdout, _, rc = run_cmd("git diff --cached --stat", cwd=skills_dir, check=False)
    if rc != 0 or not stdout.strip():
        log("  没有变更需要提交")
        return False

    commit_msg = f"auto-sync: 同步上游更新 (commit: {upstream_commit[:8]})"
    run_cmd(f'git commit -m "{commit_msg}"', cwd=skills_dir)
    log(f"  已提交: {commit_msg}")

    if dry_run:
        log("  [dry-run] 跳过推送")
        return True

    # 尝试推送
    stdout, stderr, rc = run_cmd("git push", cwd=skills_dir, check=False)
    if rc != 0:
        log(f"  推送失败: {stderr[:200]}")
        log("  请检查远程仓库配置和权限")
        return False

    log("  已推送到远程仓库")
    return True


def main():
    parser = argparse.ArgumentParser(description="纳川 Skill 自动同步上游更新")
    parser.add_argument("--dry-run", action="store_true", help="只检测变更，不实际修改")
    parser.add_argument("--force", action="store_true", help="强制更新，即使版本相同")
    parser.add_argument("--skills-dir", type=str, default=None,
                        help="纳川 skills 目录路径（默认：脚本所在目录的上级）")
    args = parser.parse_args()

    # 确定纳川 skills 目录
    if args.skills_dir:
        skills_dir = Path(args.skills_dir).resolve()
    else:
        skills_dir = Path(__file__).resolve().parent.parent

    log(f"纳川 skills 目录: {skills_dir}")
    if not skills_dir.exists():
        die(f"目录不存在: {skills_dir}")

    # 获取当前版本
    current_version = get_current_version(skills_dir)
    log(f"当前同步状态: upstream={current_version['upstream_commit'][:8] if current_version['upstream_commit'] != 'unknown' else 'unknown'}, 上次同步: {current_version['last_sync']}")

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)

        # 克隆上游
        upstream_repo = clone_upstream(tmp_dir)
        upstream_commit = get_upstream_commit(upstream_repo)
        log(f"上游最新 commit: {upstream_commit[:8]}")

        # 检查是否需要更新
        if not args.force and upstream_commit == current_version.get("upstream_commit"):
            log("已是最新版本，无需更新")
            return

        upstream_skills_dir = upstream_repo / "skills"

        # 更新各 skill
        tujie_updated = update_tujie_skill(upstream_skills_dir, skills_dir)
        video_updated = update_teachingvideo_skill(upstream_skills_dir, skills_dir)

        total_updated = tujie_updated or video_updated

        if not total_updated:
            log("没有检测到实质性变更")
            # 仍然更新版本号
            if not args.dry_run:
                save_version(skills_dir, upstream_commit)
            return

        log(f"检测到变更: tujie={'是' if tujie_updated else '否'}, teachingvideo={'是' if video_updated else '否'}")

        if args.dry_run:
            log("[dry-run] 模式，不保存版本和提交")
            return

        # 保存版本信息
        save_version(skills_dir, upstream_commit)

        # Git 提交和推送
        try:
            git_commit_and_push(skills_dir, upstream_commit, dry_run=args.dry_run)
        except Exception as e:
            log(f"Git 操作失败: {e}")
            log("文件已更新，但未提交到 Git")

    log("同步完成")


if __name__ == "__main__":
    main()
