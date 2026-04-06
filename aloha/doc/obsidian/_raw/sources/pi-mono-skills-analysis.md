---
title: PI Agent Skills 加载逻辑深度分析
date: 2026-03-30
tags:
  - AI-Agent
  - pi-mono
  - skills
  - 技术研究
---

# PI Agent (pi-mono) Skills 加载逻辑深度分析

## 一、核心实现代码分析

### 1. skills-core.js 核心模块

pi-mono/superpowers 技能系统核心实现（`lib/skills-core.js`）：

```javascript
// 五大核心函数
export {
    extractFrontmatter,    // 提取 YAML frontmatter 元数据
    findSkillsInDir,       // 递归发现技能目录
    resolveSkillPath,     // 解析技能路径（处理覆盖）
    checkForUpdates,      // 检查 Git 更新
    stripFrontmatter      // 去除 frontmatter
};
```

### 2. 技能目录结构

```
~/.config/opencode/skills/           # 个人技能（高优先级）
    └── my-skill/
        └── SKILL.md

~/.config/opencode/superpowers/skills/  # 插件技能（低优先级）
    ├── brainstorming/
    │   ├── SKILL.md
    │   ├── visual-companion.md   # 支持文档
    │   └── scripts/               # 辅助脚本
    └── ...

.project/.opencode/skills/          # 项目技能（最高优先级）
```

### 3. SKILL.md 格式（YAML Frontmatter）

```markdown
---
name: my-skill
description: Use when [condition] - [what it does]
---

# Skill Title

## Overview
Skill content...
```

---

## 二、核心函数实现逻辑

### 1. extractFrontmatter - 元数据提取

```javascript
function extractFrontmatter(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const lines = content.split('\n');
    
    let inFrontmatter = false;
    let name = '', description = '';
    
    for (const line of lines) {
        if (line.trim() === '---') {
            if (inFrontmatter) break;
            inFrontmatter = true;
            continue;
        }
        
        if (inFrontmatter) {
            const match = line.match(/^(\w+):\s*(.*)$/);
            if (match) {
                const [, key, value] = match;
                if (key === 'name') name = value.trim();
                if (key === 'description') description = value.trim();
            }
        }
    }
    return { name, description };
}
```

### 2. findSkillsInDir - 递归发现技能

```javascript
function findSkillsInDir(dir, sourceType, maxDepth = 3) {
    const skills = [];
    
    function recurse(currentDir, depth) {
        if (depth > maxDepth) return;
        
        const entries = fs.readdirSync(currentDir, { withFileTypes: true });
        for (const entry of entries) {
            if (entry.isDirectory()) {
                const skillFile = path.join(fullPath, 'SKILL.md');
                if (fs.existsSync(skillFile)) {
                    const { name, description } = extractFrontmatter(skillFile);
                    skills.push({
                        path: fullPath,
                        name: name || entry.name,
                        description,
                        sourceType
                    });
                }
                recurse(fullPath, depth + 1);  // 递归子目录
            }
        }
    }
    recurse(dir, 0);
    return skills;
}
```

### 3. resolveSkillPath - 路径解析与覆盖机制

```javascript
function resolveSkillPath(skillName, superpowersDir, personalDir) {
    const forceSuperpowers = skillName.startsWith('superpowers:');
    const actualSkillName = forceSuperpowers 
        ? skillName.replace(/^superpowers:/, '') 
        : skillName;

    // 优先级：个人技能 > superpowers技能
    if (!forceSuperpowers && personalDir) {
        const personalPath = path.join(personalDir, actualSkillName);
        if (fs.existsSync(path.join(personalPath, 'SKILL.md'))) {
            return { skillFile: ..., sourceType: 'personal', ... };
        }
    }
    
    // 回退到 superpowers
    // ...
}
```

---

## 三、pi-mono Skills 系统特点

### 1. 完整的功能特性

| 特性 | 说明 |
|------|------|
| **YAML Frontmatter** | 标准化的元数据（name, description） |
| **递归发现** | 支持嵌套目录（maxDepth=3） |
| **优先级覆盖** | 项目 > 个人 > superpowers |
| **命名空间** | 支持 `superpowers:skill-name` 前缀 |
| **支持文件** | 技能目录下可包含脚本、文档 |
| **Git 更新检查** | 启动时检查技能更新 |

### 2. 工具集成

```javascript
// use_skill 工具
{
    name: 'use_skill',
    description: 'Load and read a specific skill...',
    schema: z.object({
        skill_name: z.string()
    }),
    execute: async ({ skill_name }) => {
        const resolved = skillsCore.resolveSkillPath(skill_name, ...);
        const fullContent = fs.readFileSync(resolved.skillFile, 'utf8');
        return stripFrontmatter(fullContent);
    }
}

// find_skills 工具
{
    name: 'find_skills',
    execute: async () => {
        const skills = skillsCore.findSkillsInDir(...);
        // 返回格式化的技能列表
    }
}
```

---

## 四、与 Aloha 对比分析

### 实现差异

| 特性 | pi-mono (superpowers) | Aloha |
|------|----------------------|-------|
| **语言** | TypeScript | Python |
| **元数据格式** | YAML Frontmatter | 简单 Markdown 解析 |
| **技能发现** | 递归目录扫描 | 目录遍历 |
| **优先级机制** | 项目 > 个人 > superpowers | always_skills.txt |
| **命名空间** | 支持 `prefix:skill` | 不支持 |
| **支持文件** | 技能目录可包含脚本/文档 | 仅 SKILL.md |
| **自动更新检查** | Git fetch 检查 | 无 |
| **工具集成** | 专用 use_skill/find_skills | 手动加载 |

### 代码结构对比

**pi-mono**:
```javascript
// 独立模块化设计
lib/skills-core.js  →  核心函数库
.opencode/plugin/   →  OpenCode 插件
.skills/            →  技能定义
```

**Aloha**:
```python
# 单文件简单实现
aloha/agent/skills.py  →  SkillsLoader 类
```

### 优缺点分析

**pi-mono 优点**:
- ✅ 完整的前端系统（多平台支持：Claude Code, OpenCode, Codex）
- ✅ 标准化 YAML 格式
- ✅ 优先级覆盖机制
- ✅ Git 更新检查

**Aloha 优点**:
- ✅ 简单轻量，易于理解
- ✅ Python 生态集成
- ✅ 适合内部项目使用

---

## 五、可改进方向

参考 pi-mono 设计，Aloha 可考虑：

1. **标准化技能格式** - 添加 YAML frontmatter 支持
2. **支持技能覆盖** - 实现优先级机制（项目 > 个人 > 全局）
3. **添加工具集成** - 实现 `use_skill` / `find_skills` 工具
4. **支持辅助文件** - 技能目录包含脚本和文档
5. **自动更新检查** - Git 检查技能更新
