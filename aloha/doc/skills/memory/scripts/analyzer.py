"""代码分析器模块 - 自动分析代码特征"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any


# 语言映射
LANGUAGE_MAP: dict[str, str] = {
    ".py": "Python",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".jsx": "JavaScript (React)",
    ".tsx": "TypeScript (React)",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".kt": "Kotlin",
    ".scala": "Scala",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".less": "LESS",
    ".vue": "Vue",
    ".svelte": "Svelte",
    ".md": "Markdown",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml": "YAML",
    ".xml": "XML",
    ".sql": "SQL",
    ".sh": "Shell",
    ".bash": "Bash",
    ".ps1": "PowerShell",
    ".r": "R",
    ".lua": "Lua",
    ".ex": "Elixir",
    ".exs": "Elixir",
    ".erl": "Erlang",
    ".clj": "Clojure",
    ".hs": "Haskell",
    ".ml": "OCaml",
    ".fs": "F#",
    ".dart": "Dart",
    ".groovy": "Groovy",
    ".gradle": "Gradle",
    ".toml": "TOML",
    ".ini": "INI",
    ".cfg": "Config",
}


# 框架/库关键词映射
FRAMEWORK_KEYWORDS: dict[str, list[str]] = {
    "Django": ["django", "from django", "import django"],
    "Flask": ["flask", "from flask", "import flask"],
    "FastAPI": ["fastapi", "from fastapi", "import fastapi"],
    "React": ["react", "from react", "useState", "useEffect", "jsx"],
    "Vue": ["vue", "from vue", "vue component", "vue-router"],
    "Angular": ["angular", "@angular", "ng-module"],
    "Express": ["express", "from express", "require('express')"],
    "Node.js": ["node", "require(", "module.exports", "import from 'node"],
    "Spring": ["@spring", "@component", "@service", "springframework"],
    "Spring Boot": ["@springboot", "springboot", "spring boot"],
    "Flask": ["flask", "from flask"],
    "NumPy": ["numpy", "import numpy", "np."],
    "Pandas": ["pandas", "import pandas", "pd."],
    "TensorFlow": ["tensorflow", "import tensorflow", "tf."],
    "PyTorch": ["torch", "import torch", "nn.Module"],
    " requests": ["requests", "import requests", "urllib"],
    "FastAPI": ["fastapi", "from fastapi"],
    "Lodash": ["lodash", "_."],
    "jQuery": ["jquery", "$."],
    "Bootstrap": ["bootstrap"],
    "Tailwind": ["tailwind", "className="],
}


def detect_language(file_path: str) -> str:
    """检测文件语言类型"""
    ext = os.path.splitext(file_path)[1].lower()
    return LANGUAGE_MAP.get(ext, "Unknown")


def detect_indent_style(content: str) -> dict[str, Any]:
    """检测缩进风格"""
    lines = content.split("\n")
    space_counts: dict[int, int] = {}
    tab_count = 0

    for line in lines:
        if not line or line.strip() == "":
            continue

        # 计算前导空格
        leading_spaces = len(line) - len(line.lstrip())
        if line.startswith("\t"):
            tab_count += 1
        elif leading_spaces > 0:
            space_counts[leading_spaces] = space_counts.get(leading_spaces, 0) + 1

    # 找出最常见的缩进
    if space_counts:
        most_common = max(space_counts, key=space_counts.get)
        return {"type": "spaces", "size": most_common}
    elif tab_count > 0:
        return {"type": "tabs", "size": 1}

    return {"type": "unknown", "size": 0}


def detect_naming_convention(content: str) -> list[str]:
    """检测命名规范"""
    conventions: list[str] = []

    # 提取标识符
    identifiers = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", content)

    snake_case = 0
    camelCase = 0
    PascalCase = 0
    kebab_case = 0

    for name in identifiers:
        if len(name) < 3:
            continue

        if "_" in name and name.islower():
            snake_case += 1
        elif name.replace("_", "").islower() and "_" not in name:
            camelCase += 1
        elif name[0].isupper() and name[1:].replace("_", "").islower():
            PascalCase += 1
        elif "-" in name and name.islower():
            kebab_case += 1

    total = snake_case + camelCase + PascalCase + kebab_case
    if total == 0:
        return ["unknown"]

    threshold = total * 0.3  # 30% 阈值

    if snake_case > threshold:
        conventions.append("snake_case")
    if camelCase > threshold:
        conventions.append("camelCase")
    if PascalCase > threshold:
        conventions.append("PascalCase")
    if kebab_case > threshold:
        conventions.append("kebab-case")

    return conventions if conventions else ["unknown"]


def detect_comment_style(content: str, language: str) -> str:
    """检测注释风格"""
    # 单行注释
    single_comment_patterns = {
        "#": r"^\s*#",
        "//": r"^\s*//",
        "--": r"^\s*--",
        ";": r"^\s*;",
        "--": r"^\s*--",
    }

    # 多行注释
    multi_comment_patterns = {
        '"""': r'"""',
        "'''": r"'''",
        "/*": r"/\*",
    }

    # 统计注释类型
    comment_counts: dict[str, int] = {}

    for comment_type, pattern in single_comment_patterns.items():
        count = len(re.findall(pattern, content, re.MULTILINE))
        if count > 0:
            comment_counts[comment_type] = count

    for comment_type, pattern in multi_comment_patterns.items():
        count = len(re.findall(pattern, content))
        if count > 0:
            comment_counts[comment_type] = count

    if not comment_counts:
        return "none"

    # 找出最常用的注释类型
    most_common = max(comment_counts, key=comment_counts.get)

    comment_style_map = {
        "#": "Python/Shell 风格 (#)",
        "//": "C/C++/Java/JavaScript 风格 (//)",
        "--": "SQL/Lua 风格 (--)",
        ";": "Assembly/Config 风格 (;)",
        '"""': "Python docstring (\"\"\")",
        "'''": "Python docstring (''')",
        "/*": "C 风格 block comment",
    }

    return comment_style_map.get(most_common, most_common)


def extract_imports(content: str, language: str) -> list[str]:
    """提取导入语句"""
    imports: list[str] = []

    if language == "Python":
        # from x import y / import x
        patterns = [
            r"^from\s+([\w.]+)\s+import",
            r"^import\s+([\w.]+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)

    elif language in ("JavaScript", "TypeScript", "JavaScript (React)", "TypeScript (React)"):
        # import x from 'y' / require('x')
        patterns = [
            r"^import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]",
            r"^import\s+['\"]([^'\"]+)['\"]",
            r"require\s*\(\s*['\"]([^'\"]+)['\"]\s*\)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            imports.extend(matches)

    elif language == "Java":
        # import x.y.z;
        matches = re.findall(r"^import\s+([\w.]+);", content, re.MULTILINE)
        imports.extend(matches)

    elif language == "Go":
        # import "x" / import (
        matches = re.findall(r'import\s+"([^"]+)"', content)
        imports.extend(matches)

    elif language == "Rust":
        # use x::y;
        matches = re.findall(r"^use\s+([\w:]+)", content, re.MULTILINE)
        imports.extend(matches)

    return list(set(imports))  # 去重


def detect_frameworks(imports: list[str]) -> list[str]:
    """根据导入检测框架/库"""
    frameworks: set[str] = set()

    content = " ".join(imports).lower()

    for framework, keywords in FRAMEWORK_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in content:
                frameworks.add(framework)
                break

    return list(frameworks)


def analyze_file(file_path: str) -> dict[str, Any]:
    """分析单个文件"""
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            return {"error": f"Cannot read file: {e}"}

    language = detect_language(file_path)
    indent = detect_indent_style(content)
    naming = detect_naming_convention(content)
    comment_style = detect_comment_style(content, language)
    imports = extract_imports(content, language)
    frameworks = detect_frameworks(imports)

    return {
        "file": file_path,
        "language": language,
        "indent_style": indent,
        "naming_conventions": naming,
        "comment_style": comment_style,
        "imports": imports[:20],  # 限制数量
        "frameworks": frameworks,
    }


def analyze_project_structure(project_root: str) -> dict[str, Any]:
    """分析项目目录结构"""
    structure: dict[str, Any] = {
        "root": project_root,
        "directories": [],
        "config_files": [],
        "entry_points": [],
    }

    # 常见入口文件
    entry_patterns = [
        "main.py",
        "app.py",
        "index.js",
        "index.ts",
        "server.js",
        "main.go",
        "main.rs",
        "main.java",
        "App.vue",
        "main.tsx",
    ]

    for root, dirs, files in os.walk(project_root):
        # 跳过隐藏目录和常见忽略目录
        dirs[:] = [d for d in dirs if not d.startswith(".") and d not in ("node_modules", "__pycache__", "venv", ".venv")]

        rel_root = os.path.relpath(root, project_root)
        if rel_root != ".":
            structure["directories"].append(rel_root)

        for f in files:
            if f in entry_patterns:
                structure["entry_points"].append(os.path.join(rel_root, f))

            # 配置文件
            if f in ("package.json", "requirements.txt", "Pipfile", "pyproject.toml", "setup.py", "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "tsconfig.json", "webpack.config.js", "vite.config.ts", ".env", "docker-compose.yml"):
                structure["config_files"].append(f)

    return structure


def full_analysis(file_path: str) -> dict[str, Any]:
    """完整分析：文件 + 项目结构"""
    file_analysis = analyze_file(file_path)

    if "error" in file_analysis:
        return file_analysis

    project_root = os.path.dirname(os.path.abspath(file_path))
    project_structure = analyze_project_structure(project_root)

    return {
        "file_analysis": file_analysis,
        "project_structure": project_structure,
    }
