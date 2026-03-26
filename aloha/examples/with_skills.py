"""Aloha Skills 使用示例

演示如何使用 SkillsLoader 加载和管理技能。
"""

import os
from pathlib import Path

from aloha import ReActLoop, OpenAIProvider, SkillsLoader
from aloha.bus import MessageBus


async def main():
    """主函数"""
    # 创建 skills workspace
    workspace = Path("~/.aloha/workspace").expanduser()
    skills_dir = workspace / "skills"

    # 创建示例技能目录
    github_skill_dir = skills_dir / "github"
    github_skill_dir.mkdir(parents=True, exist_ok=True)

    # 创建 SKILL.md 文件
    skill_content = """# GitHub Skill

你可以通过 GitHub API 来管理代码仓库。

## 可用功能

- 搜索仓库
- 获取仓库信息
- 创建 issue

## 使用方法

当用户请求与 GitHub 相关时，使用此技能。
"""

    (github_skill_dir / "SKILL.md").write_text(skill_content, encoding="utf-8")

    # 创建 always_skills.txt
    (skills_dir / "always_skills.txt").write_text("github\n", encoding="utf-8")

    # 加载技能
    loader = SkillsLoader(workspace)

    # 列出所有技能
    print("=== 可用技能 ===")
    skills = loader.list_skills()
    for skill in skills:
        print(f"- {skill['name']}: {skill['description']}")

    # 构建技能摘要
    print("\n=== 技能摘要 ===")
    summary = loader.build_skills_summary()
    print(summary)

    # 获取始终激活的技能
    print("\n=== 始终激活的技能 ===")
    always = loader.get_always_skills()
    print(always)

    # 加载技能内容
    print("\n=== GitHub 技能内容 ===")
    content = loader.load_skill("github")
    if content:
        print(content[:200] + "...")
    else:
        print("未找到技能内容")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
