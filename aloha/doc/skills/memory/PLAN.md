# Roo Code 记忆功能实现计划

## 文件结构

```
C:\Users\linbirg\.roo\skills\memory\
├── PLAN.md           # 本计划文档
├── SPEC.md           # 设计文档
├── SKILL.md          # Skill 定义
└── scripts\
    ├── __init__.py
    ├── memory.py     # 记忆核心逻辑
    ├── analyzer.py   # 代码分析器
    └── config.py     # 配置管理
```

## 任务分解

### 任务1: 创建 Skill 目录和初始化文件
- [ ] 创建 `scripts/__init__.py`
- [ ] 创建基础目录结构

### 任务2: 实现配置管理模块
- [ ] 创建 `scripts/config.py`
  - 读取/写入 config.yaml
  - 提供默认配置
  - 获取记忆文件路径

### 任务3: 实现代码分析器
- [ ] 创建 `scripts/analyzer.py`
  - `detect_language(file_path)` - 检测编程语言
  - `detect_indent_style(content)` - 检测缩进风格
  - `detect_naming_convention(content)` - 检测命名规范
  - `extract_imports(content, language)` - 提取依赖
  - `analyze_structure(project_root)` - 分析项目结构
  - `full_analysis(file_path)` - 完整分析

### 任务4: 实现记忆核心模块
- [ ] 创建 `scripts/memory.py`
  - `load_longterm()` - 加载长期记忆
  - `load_session()` - 加载会话记忆
  - `save_longterm(data)` - 保存长期记忆
  - `save_session(data)` - 保存会话记忆
  - `merge_to_longterm()` - 合并会话到长期
  - `clear_session()` - 清除会话记忆
  - `show_memory()` - 显示当前记忆
  - `analyze_and_update(file_path)` - 分析并更新记忆

### 任务5: 编写 Skill 定义
- [ ] 创建 `SKILL.md`
  - 定义 skill 名称和描述
  - 定义触发关键词
  - 定义手动指令（/memory show/clear/save）
  - 配置自动触发规则

### 任务6: 创建初始配置文件
- [ ] 创建 `config.yaml` 模板
  - 配置存储路径
  - 配置自动加载/保存
  - 配置忽略文件模式

## 实现步骤

### Step 1: 创建目录结构
```bash
mkdir -p C:\Users\linbirg\.roo\skills\memory\scripts
```

### Step 2: 实现 config.py
```python
# 伪代码
class Config:
    def __init__(self, workspace_root):
        self.config_path = os.path.join(workspace_root, '.roo', 'memory', 'config.yaml')
    
    def load(self):
        # 加载或创建默认配置
    
    def get_memory_path(self):
        # 返回记忆文件路径
```

### Step 3: 实现 analyzer.py
```python
# 伪代码
def detect_language(file_path):
    ext = os.path.splitext(file_path)[1]
    return LANGUAGE_MAP.get(ext, 'unknown')

def detect_indent_style(content):
    # 统计空格和 tab 数量
    # 返回 '2 spaces', '4 spaces', 'tabs'
```

### Step 4: 实现 memory.py
```python
# 伪代码
def load_memory(memory_type='both'):
    if memory_type in ('both', 'longterm'):
        # 读取 longterm.md
    if memory_type in ('both', 'session'):
        # 读取 session.md
    return merged_content

def update_memory(file_path):
    analysis = analyze_code(file_path)
    # 更新记忆文件
```

### Step 5: 编写 SKILL.md
```markdown
---
name: memory
description: Roo Code 记忆功能 - 自动记住代码风格、技术栈和项目结构
---

# Memory Skill

## 触发条件
- 手动：/memory [command]
- 自动：[配置后文件保存时]

## 指令
- /memory show - 显示当前记忆
- /memory clear - 清除会话记忆
- /memory save - 保存到长期记忆
```

## 验收标准

1. Skill 可以被 Roo Code 加载
2. `/memory show` 指令可以显示记忆内容
3. 可以分析代码文件并提取特征
4. 记忆可以跨会话持久化
5. 配置文件可以自定义
