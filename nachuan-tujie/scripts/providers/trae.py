"""
TRAE 内置生图 Provider —— 零配置免 API Key 模式。

工作原理：
- 不调用外部 HTTP API，而是利用 TRAE 环境内置的 GenerateImage 工具
- create_task(): 将 prompt 写入输出目录下的 .prompt 文件，生成一个"任务描述文件"
- poll_task(): 检查输出目录下是否已存在生成的图片（由 agent 通过 GenerateImage 工具生成后放入）
- 实际的图片生成由 agent 调用 GenerateImage 工具完成，本 provider 只做"任务编排 + 文件交接"

使用场景：
- 用户未配置任何 API Key 时自动降级使用
- SKILL.md 工作流中明确说明：trae 模式下需要 agent 手动调用 GenerateImage 工具
- 适合教育场景：零门槛使用，不需要用户申请外部 API

文件约定（任务生命周期）：
  {output_dir}/
    {task_id}.prompt        ← create_task 写入的 prompt + 参数
    {task_id}.status        ← 状态文件（pending / generating / completed / failed）
    {task_id}.png           ← agent 生成后放入的图片（poll_task 检测到即完成）
    {task_id}.json          ← 任务元数据
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional

from .base import BaseProvider


# aspect_ratio → GenerateImage image_size 映射
ASPECT_TO_SIZE = {
    "9:16": "portrait_16_9",    # 720x1280 竖版
    "16:9": "landscape_16_9",   # 1280x720 横版
    "1:1": "square",            # 1024x1024 方形
    "4:3": "landscape_4_3",     # 1152x864
    "3:4": "portrait_4_3",      # 864x1152
}


class TraeProvider(BaseProvider):
    """
    TRAE 内置生图 Provider。

    特点：
    - 不需要 API Key（requires_api_key = False）
    - 不发起 HTTP 请求，通过文件系统与 agent 协作
    - create_task 生成任务描述文件并打印 GenerateImage 调用指引
    - poll_task 轮询输出目录中的图片文件
    """

    env_var = ""  # 不需要环境变量
    requires_api_key = False
    POLL_INTERVAL = 3  # 轮询间隔更短，因为是本地文件检测
    POLL_MAX_TIMES = 200  # 最多等 10 分钟（agent 手动操作可能较慢）

    def __init__(self, api_key: str = "", output_dir: Optional[str] = None):
        super().__init__(api_key)
        self._output_dir = Path(output_dir or "./output")
        self._output_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # 对外 API：与 BaseProvider 接口一致
    # ----------------------------------------------------------

    def create_task(
        self, prompt: str, mode: str,
        images: Optional[list[str]] = None,
        aspect_ratio: str = "16:9", resolution: str = "2K",
    ) -> Optional[str]:
        """
        创建"任务"：写入 prompt 文件，打印 agent 操作指引。
        返回 task_id（基于 UUID）。
        """
        task_id = f"trae-{uuid.uuid4().hex[:12]}"
        image_size = ASPECT_TO_SIZE.get(aspect_ratio, "portrait_16_9")

        # 写入 prompt 文件
        prompt_path = self._output_dir / f"{task_id}.prompt"
        prompt_path.write_text(prompt, encoding="utf-8")

        # 写入状态文件
        status_path = self._output_dir / f"{task_id}.status"
        status_path.write_text("pending", encoding="utf-8")

        # 写入元数据
        meta = {
            "task_id": task_id,
            "mode": mode,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "image_size": image_size,
            "images": images or [],
            "prompt_path": str(prompt_path),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        meta_path = self._output_dir / f"{task_id}.json"
        meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

        # 打印 GenerateImage 工具调用指引（agent 看到后应执行）
        self._print_generate_image_guide(task_id, prompt, image_size, mode, images)

        return task_id

    def poll_task(self, task_id: str, mode: str) -> Optional[dict]:
        """
        轮询任务：检查输出目录中是否已存在 {task_id}.png。
        找到则返回 {"images": [local_path]}；超时返回 None。
        """
        print(f"    [trae provider] 等待 agent 生成图片，task_id={task_id}")
        print(f"    [trae provider] 请使用 GenerateImage 工具生成图片，并保存为:")
        print(f"                    {self._output_dir / task_id}.png")

        image_path = self._output_dir / f"{task_id}.png"

        for i in range(self.POLL_MAX_TIMES):
            time.sleep(self.POLL_INTERVAL)
            elapsed = (i + 1) * self.POLL_INTERVAL

            # 检查图片是否已存在
            if image_path.exists() and image_path.stat().st_size > 0:
                # 更新状态
                status_path = self._output_dir / f"{task_id}.status"
                status_path.write_text("completed", encoding="utf-8")
                print(f"    ✓ 检测到生成的图片,耗时约 {elapsed}s")
                print(f"      📁 {image_path} ({image_path.stat().st_size // 1024} KB)")
                return {"images": [str(image_path.resolve())]}

            # 检查是否有失败标记
            fail_path = self._output_dir / f"{task_id}.failed"
            if fail_path.exists():
                reason = fail_path.read_text(encoding="utf-8").strip() or "未知原因"
                print(f"    ✗ 任务失败: {reason}")
                return None

            if (i + 1) % 10 == 0:
                print(f"    [已等 {elapsed}s] 等待图片生成中...")

        print(f"    ✗ 轮询超时({self.POLL_MAX_TIMES * self.POLL_INTERVAL}s)")
        return None

    # ----------------------------------------------------------
    # BaseProvider 抽象方法实现（trae 模式不直接用 HTTP，所以部分方法留空/返回默认值）
    # ----------------------------------------------------------

    def build_create_payload(
        self, prompt: str, mode: str, images: Optional[list[str]],
        aspect_ratio: str, resolution: str,
    ) -> tuple[str, dict]:
        # trae 模式不使用 HTTP，此方法不会被调用（create_task 已重写）
        return "", {"prompt": prompt, "mode": mode}

    def parse_task_id(self, resp: dict) -> Optional[str]:
        return None  # 不会被调用

    def build_poll_url(self, task_id: str, mode: str) -> str:
        return ""  # 不会被调用

    def parse_poll_status(self, resp: dict) -> tuple[str, dict]:
        return "polling", {}  # 不会被调用

    def extract_images(self, poll_body: dict) -> list[str]:
        return []  # 不会被调用

    # ----------------------------------------------------------
    # 内部方法
    # ----------------------------------------------------------

    def _print_generate_image_guide(
        self, task_id: str, prompt: str, image_size: str,
        mode: str, images: Optional[list[str]],
    ) -> None:
        """打印 GenerateImage 工具调用指引，供 agent 参考。"""
        print()
        print("=" * 60)
        print("  🎨 TRAE 内置生图模式（零配置）")
        print("=" * 60)
        print(f"  task_id     : {task_id}")
        print(f"  模式        : {mode}")
        print(f"  尺寸        : {image_size}")
        print(f"  输出路径    : {self._output_dir / task_id}.png")
        print()
        print("  请使用 GenerateImage 工具生成图片：")
        print()
        print(f'  prompt: "{prompt[:100]}{"..." if len(prompt) > 100 else ""}"')
        print(f'  path  : {self._output_dir / task_id}')
        print(f'  size  : {image_size}')
        print()
        print("  生成完成后，图片将被自动检测到。")
        print("=" * 60)
        print()
