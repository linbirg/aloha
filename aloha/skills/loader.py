"""Skills Loader - 技能加载器

参照 nanobot 的 SkillsLoader 设计，管理 agent 的技能。
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Skill:
    """技能定义"""
    name: str
    description: str
    path: Path
    source: str = "file"  # "file" or "builtin"
    content: str | None = None


class SkillsLoader:
    """技能加载器

    从 workspace 目录加载技能文件。
    技能文件格式为 SKILL.md，包含技能的描述和使用方法。
    """

    def __init__(self, workspace: Path | str = Path("~/.aloha/workspace").expanduser()):
        self.workspace = Path(workspace)
        self.skills_dir = self.workspace / "skills"

    def list_skills(self, filter_unavailable: bool = True) -> list[dict[str, Any]]:
        """列出所有可用的技能"""
        skills = []

        if not self.skills_dir.exists():
            return skills

        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    content = skill_file.read_text(encoding="utf-8")
                    description = self._extract_description(content)

                    skill = {
                        "name": skill_path.name,
                        "description": description,
                        "path": str(skill_path),
                        "source": "file",
                        "available": True,
                    }
                    skills.append(skill)

        return skills

    def load_skill(self, name: str) -> str | None:
        """加载指定技能的内容"""
        skill_path = self.skills_dir / name / "SKILL.md"
        if skill_path.exists():
            return skill_path.read_text(encoding="utf-8")
        return None

    def load_skills_for_context(self, skill_names: list[str]) -> str:
        """加载多个技能的内容用于上下文"""
        contents = []
        for name in skill_names:
            content = self.load_skill(name)
            if content:
                contents.append(f"<!-- Skill: {name} -->\n{content}")
        return "\n\n".join(contents)

    def build_skills_summary(self) -> str:
        """构建技能的 XML 摘要（用于提示词）"""
        skills = self.list_skills()

        lines = ["<skills>"]
        for skill in skills:
            lines.append(f'  <skill available="{skill["available"]}">')
            lines.append(f'    <name>{skill["name"]}</name>')
            lines.append(f'    <description>{skill["description"]}</description>')
            lines.append(f'    <location>{skill["path"]}</location>')
            lines.append("  </skill>")
        lines.append("</skills>")

        return "\n".join(lines)

    def get_always_skills(self) -> list[str]:
        """获取始终激活的技能列表"""
        always_file = self.skills_dir / "always_skills.txt"
        if always_file.exists():
            content = always_file.read_text(encoding="utf-8")
            return [line.strip() for line in content.split("\n") if line.strip()]
        return []

    def _extract_description(self, content: str) -> str:
        """从 SKILL.md 内容中提取描述"""
        lines = content.split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith("# "):
                # 跳过标题，返回后续内容作为描述
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return content[:200] if len(content) > 200 else content
