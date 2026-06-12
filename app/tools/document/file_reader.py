"""
============================================================================
文件读取工具 - 读取本地文件内容
============================================================================
支持文本文件读取，可指定起始行和行数限制。
"""
import os
from pathlib import Path
from typing import Any, Dict
from app.tools.base import BaseTool, validate_params


class FileReaderTool(BaseTool):
    """文件读取工具 - 读取本地文本文件内容"""

    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return (
            "读取指定路径的本地文本文件内容。"
            "支持指定读取的起始行(start_line)和最大行数(max_lines)限制。"
            "适用场景：查看代码文件、配置文件、日志文件等。"
        )

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要读取的文件路径（绝对路径或相对于项目的路径）"
                },
                "start_line": {
                    "type": "number",
                    "description": "从第几行开始读取（从1开始），默认1"
                },
                "max_lines": {
                    "type": "number",
                    "description": "最多读取多少行，默认50行，最大100行"
                },
            },
            "required": ["file_path"],
        }

    @validate_params
    async def execute(
        self,
        file_path: str = "",
        start_line: int = 1,
        max_lines: int = 50
    ) -> str:
        """执行文件读取"""
        # 安全检查：限制读取行数
        max_lines = min(max(max_lines, 1), 100)
        start_line = max(start_line, 1)

        # 路径解析
        path = Path(file_path)
        if not path.is_absolute():
            # 相对路径：以项目根目录为基准
            from app.core.config import PROJECT_ROOT
            path = PROJECT_ROOT / file_path

        if not path.exists():
            return f"文件不存在: {path}"

        if not path.is_file():
            return f"路径不是文件: {path}"

        # 安全检查：限制文件大小（最大10MB），拒绝二进制文件
        file_size = path.stat().st_size
        if file_size > 10 * 1024 * 1024:
            return f"文件过大（{file_size / 1024 / 1024:.1f}MB），最大支持10MB。"

        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
        except Exception as e:
            return f"读取文件失败: {e}"

        total_lines = len(lines)
        end_line = min(start_line + max_lines - 1, total_lines)
        selected = lines[start_line - 1 : end_line]

        # 格式化输出（带行号）
        output_lines = []
        for i, line in enumerate(selected, start=start_line):
            output_lines.append(f"{i:4d}| {line.rstrip()}")

        result = "\n".join(output_lines)
        if end_line < total_lines:
            result += f"\n... (共 {total_lines} 行，已显示 {start_line}-{end_line} 行)"

        return result

from app.tools.registry import tool_registry
tool_registry.register(FileReaderTool())
