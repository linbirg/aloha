# Windows Terminal 完全配置指南

> **目标读者**：程序员 / 开发者
> **侧重点**：提升开发效率，包含 WSL2 深度集成 + VSCode 联动
> **系统要求**：Windows 10 1903+ / Windows 11
> **最后更新**：2026-04

---

## 前言

Windows Terminal 是微软 2019 年推出的现代化终端，相比传统的 `cmd.exe` 和 `PowerShell`，它在**性能、界面、多标签页、分屏**等核心体验上有质的飞跃。对于需要同时操作 WSL2、SSH 跳板机、PowerShell 的开发者而言，一个配置良好的 Windows Terminal 可以显著提升日常效率。

本指南聚焦**开发效率**，覆盖：安装配置、多 Profile 管理、热键绑定、Oh-My-Posh 主题、Nerd Fonts、WSL2 深度集成、VSCode 联动，以及性能调优。

---

## 第一章：安装 Windows Terminal

### 1.1 推荐方式：winget（命令行，一行搞定）

Windows 10 1903+ 和 Windows 11 自带 `winget` 包管理器：

```powershell
winget install Microsoft.WindowsTerminal
```

安装完成后，在开始菜单搜索 `Windows Terminal` 即可启动。

### 1.2 Microsoft Store

访问 [Microsoft Store - Windows Terminal](https://aka.ms/terminal)，点击安装。适合不熟悉命令行的用户，Store 会自动推送更新。

### 1.3 GitHub Releases（离线环境）

访问 [microsoft/terminal/releases](https://github.com/microsoft/terminal/releases)，下载最新的 `.msixbundle` 文件，双击安装。适合无法访问 Store 的内网环境。

### 1.4 验证版本

打开 Windows Terminal，点击左上角 `⌘` 或 `↓`，查看版本号。2024 年后稳定版为 **1.19+**。

---

## 第二章：熟悉界面与核心概念

### 2.1 四个核心概念

| 概念 | 说明 |
|------|------|
| **Tab（标签页）** | 多个终端实例共存于一个窗口 |
| **Pane（窗格）** | 在同一 Tab 内水平或垂直分屏 |
| **Profile（配置文件）** | 每个终端实例的启动配置（程序、配色、字体等）|
| **Drop-down Menu（下拉菜单）** | 点击窗口顶部箭头，切换 Profile |

### 2.2 必知快捷键

| 操作 | 快捷键 |
|------|--------|
| 新建标签页 | `Ctrl + Shift + T` |
| 关闭标签页 | `Ctrl + Shift + W` |
| 打开命令面板 | `Ctrl + Shift + P` |
| 打开设置（settings.json）| `Ctrl + ,` |
| 复制选中内容 | 直接鼠标选中（无需额外按键）|
| 粘贴 | `Ctrl + Shift + V` |
| 新建垂直分屏 | `Alt + Shift + +` |
| 新建水平分屏 | `Alt + Shift + -` |
| 切换窗格焦点 | `Alt + ↑ ↓ ← →` |
| 最大化当前窗格 | `Alt + Shift + Z` |
| 关闭窗格 | `Ctrl + Shift + W`（同标签页）|

### 2.3 settings.json 认知

Windows Terminal 有两个配置文件：

- **`defaults.json`**：微软出厂默认值，**不可修改**，记录了所有内置 Profile 和配色方案
- **`settings.json`**（用户配置）：**我们的主战场**，通过 `Ctrl + ,` 打开，优先级高于 defaults.json

> **原则**：永远只修改 `settings.json`，不碰 `defaults.json`。

---

## 第三章：settings.json 核心配置

### 3.1 全局设置（globals）

打开 `settings.json`，顶层对象即 `globals`，控制整个终端的行为：

```json
{
  "$schema": "https://aka.ms/terminal-profiles-schema",
  "defaultProfile": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}",
  "copyOnSelect": false,
  "copyFormatting": false,
  "theme": "dark",
  "showTabsInTitlebar": true,
  "snapToGridOnResize": true,
  "initialPosition": "100,100",
  "initialSize": 900,
  "language": "zh-CN"
}
```

| 配置项 | 说明 | 推荐值 |
|--------|------|--------|
| `defaultProfile` | 默认启动的 Profile 的 GUID | 按需设置 |
| `copyOnSelect` | 选中即复制到剪贴板 | `false`（避免误触）|
| `copyFormatting` | 复制时包含颜色格式 | `false` |
| `theme` | 窗口主题 | `"dark"` / `"light"` / `"system"` |
| `showTabsInTitlebar` | Tab 显示在标题栏 | `true` |

### 3.2 Profile 详解：PowerShell 示例

每个 Profile 是一个完整的终端配置。以下是一个优化过的 PowerShell Profile：

```json
{
  "guid": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}",
  "name": "PowerShell",
  "commandline": "powershell.exe",
  "startingDirectory": "%USERPROFILE%",
  "icon": "ms-appx:///ProfileIcons/{61c54bbd-c2c6-5271-96e7-009a87ff44bf}.png",
  "fontFace": "CaskaydiaCove NF",
  "fontSize": 12,
  "cursorColor": "#FFFFFF",
  "cursorShape": "bar",
  "padding": "8, 4, 8, 4",
  "snapOnInput": true,
  "tabTitle": "PowerShell",
  "colorScheme": "One Half Dark"
}
```

**关键字段说明：**

| 字段 | 说明 |
|------|------|
| `guid` | 全局唯一标识符，用于 `defaultProfile` 引用 |
| `name` | 下拉菜单中显示的名称 |
| `commandline` | 启动的可执行文件路径 |
| `startingDirectory` | 启动时的初始目录（支持 WSL 路径如 `\\wsl$\Ubuntu\home`）|
| `fontFace` | 字体（需要安装 Nerd Fonts 才生效，见第六章）|
| `cursorShape` | 光标形状：`"bar"` 条状 / `"underscore"` 下划线 / `"box"` 方块 / `"circle"` 圆形 |
| `colorScheme` | 引用的配色方案名称 |

### 3.3 内置配色方案

Windows Terminal 内置了多套经典配色，通过在 Profile 中引用 `colorScheme` 使用：

| 方案名称 | 风格 |
|---------|------|
| `Campbell` | 经典 CMD 风格 |
| `One Half Dark` | Atom One Dark 风格，适合程序员 |
| `Solarized Dark` | 护眼绿底色 |
| `Tango Dark` | 传统 Linux 桌面风格 |
| `Vintage` | 复古绿字黑底 |

**在 Profile 中激活：**

```json
"colorScheme": "One Half Dark"
```

**如果需要自定义配色**，在 `schemes` 数组中添加：

```json
{
  "name": "MyTheme",
  "black": "#1f1f1f",
  "red": "#f92672",
  "green": "#a6e22e",
  "yellow": "#e6db74",
  "blue": "#6699df",
  "purple": "#ae81ff",
  "cyan": "#66d9ef",
  "white": "#f8f8f2",
  "brightBlack": "#75715e",
  "brightRed": "#f92672",
  "brightGreen": "#a6e22e",
  "brightYellow": "#e6db74",
  "brightBlue": "#6699df",
  "brightPurple": "#ae81ff",
  "brightCyan": "#66d9ef",
  "brightWhite": "#f8f8f2",
  "background": "#1f1f1f",
  "foreground": "#f8f8f2"
}
```

---

## 第四章：多 Profile 配置（程序员必备）

### 4.1 PowerShell 7（pwsh）

PowerShell 7 是跨平台版（`pwsh`），与 Windows 自带的 PowerShell 5.1（`powershell.exe`）并存。Windows 11 内置 PowerShell 7，Windows 10 需手动安装：

```powershell
winget install Microsoft.PowerShell
```

安装后在 Profile 中添加：

```json
{
  "guid": "{7a0a52c8-1234-5678-9abc-def012345678}",
  "name": "PowerShell 7",
  "commandline": "pwsh.exe",
  "startingDirectory": "%USERPROFILE%",
  "icon": "ms-appx:///ProfileIcons/{7a0a52c8-1234-5678-9abc-def012345678}.png",
  "fontFace": "CaskaydiaCove NF",
  "fontSize": 12,
  "colorScheme": "One Half Dark",
  "cursorShape": "bar"
}
```

**同时保留 PowerShell 5.1**（有些旧脚本依赖它），在下拉菜单中切换使用。

### 4.2 Windows Terminal + WSL2 深度集成

#### 4.2.1 安装 WSL2

以管理员身份打开 PowerShell：

```powershell
wsl --install
```

重启电脑后，Ubuntu 会自动安装并创建默认用户。

#### 4.2.2 在 Windows Terminal 中添加 WSL Profile

新版 Windows Terminal 会**自动检测已安装的 WSL 发行版**，无需手动添加。如果下拉菜单中没有，手动添加：

```json
{
  "guid": "{c6eaf9f0-1234-5678-9abc-def012345679}",
  "name": "Ubuntu",
  "source": "Windows.Terminal.Wsl",
  "startingDirectory": "\\\\wsl$\\Ubuntu\\home\\用户名"
}
```

`source: "Windows.Terminal.Wsl"` 是微软推荐的自动发现方式，会自动关联 WSL 发行版。

#### 4.2.3 WSL2 与 Windows 文件系统互访

| 场景 | 路径 |
|------|------|
| 在 WSL 内访问 Windows D 盘 | `/mnt/d/` |
| 在 Windows 内访问 WSL Ubuntu home | `\\wsl$\Ubuntu\home\` |
| 在 Windows 内访问 WSL 根目录 | `\\wsl$\Ubuntu\` |

> **技巧**：在 Windows 文件资源管理器地址栏输入 `\\wsl$`，可直接浏览所有 WSL 发行版的文件系统。

#### 4.2.4 解决 WSL2 启动目录重置问题

WSL2 默认启动目录是 WSL 内部的用户 home 目录，不会跟随 Windows Terminal 设置。用以下方式强制指定启动目录：

```json
"startingDirectory": "\\\\wsl$\\Ubuntu\\home\\用户名"
```

注意：**必须使用 UNC 路径**（`\\wsl$\Ubuntu\...`），普通 Linux 路径会被 WSL 重置。

#### 4.2.5 WSL2 + Oh-My-Posh 统一主题（可选）

WSL2 内的 Linux shell 主题独立于 Windows Terminal 配色。在 WSL 内部安装 Oh-My-Posh（见第六章），可以实现 WSL 和 PowerShell 两端提示符风格统一。

### 4.3 SSH Profile（跳板机场景）

#### 4.3.1 直接 SSH 连接

```json
{
  "guid": "{a1b2c3d4-1234-5678-9abc-def012345680}",
  "name": "SSH - 生产服务器",
  "commandline": "ssh user@192.168.1.100",
  "tabTitle": "🚀 prod-server",
  "colorScheme": "Campbell",
  "fontFace": "CaskaydiaCove NF"
}
```

#### 4.3.2 SSH 跳板机（二跳）

```json
{
  "name": "SSH - 内网跳板",
  "commandline": "ssh -J user@bastion.com user@internal-host",
  "tabTitle": "🔒 内网机器"
}
```

> **建议**：给每个 SSH Profile 加上表情前缀（🚀 / 🔒 / 🧪），在多标签页切换时一目了然。

#### 4.3.3 通过 tabTitle 标注环境颜色

Windows Terminal 支持在标签页标题显示当前环境。用变量 `$(whoami)@$(hostname)` 可以显示登录信息：

```json
"tabTitle": "🚀 prod - $(whoami)@$(hostname)"
```

### 4.4 Anaconda 环境 Profile

激活 conda 环境时指定启动目录：

```json
{
  "name": "Conda - py38",
  "commandline": "cmd.exe /k conda activate py38 && cd /d D:\\workspace",
  "tabTitle": "🐍 py38"
}
```

### 4.5 CMD.exe（兼容旧脚本）

Windows Terminal 保留 CMD Profile，确保老批处理脚本正常运行：

```json
{
  "guid": "{0caa0dad-35be-5f56-a8ff-afceeeaa6101}",
  "name": "CMD",
  "commandline": "cmd.exe",
  "hidden": false
}
```

---

## 第五章：热键绑定（keybindings）

### 5.1 默认热键一览

| 分类 | 操作 | 默认快捷键 |
|------|------|-----------|
| **标签页** | 新建 | `Ctrl + Shift + T` |
| | 关闭 | `Ctrl + Shift + W` |
| | 切换（左右）| `Ctrl + Alt + ←/→` |
| | 切换（循环）| `Ctrl + Tab / Ctrl + Shift + Tab` |
| **窗格** | 垂直分屏 | `Alt + Shift + +` |
| | 水平分屏 | `Alt + Shift + -` |
| | 切换焦点 | `Alt + ↑ ↓ ← →` |
| | 最大化 | `Alt + Shift + Z` |
| **复制粘贴** | 复制（选中即复制）| 鼠标选中即可 |
| | 粘贴 | `Ctrl + Shift + V` |
| | 粘贴（传统）| `Ctrl + V` |
| **搜索** | 全局搜索 | `Ctrl + Shift + F` |
| **面板** | 打开命令面板 | `Ctrl + Shift + P` |
| | 设置 | `Ctrl + ,` |
| **其他** | 切换全屏 | `F11` |
| | 复制标签页（克隆）| `Ctrl + Shift + D` |

### 5.2 自定义热键（推荐配置）

将以下 JSON 添加到 `settings.json` 的 `keybindings` 数组中，**覆盖默认值**：

```json
"keybindings": [
  {
    "command": "copy",
    "singleLine": false,
    "keys": "ctrl+c"
  },
  {
    "command": "paste",
    "keys": "ctrl+v"
  },
  {
    "command": "find",
    "keys": "ctrl+shift+f"
  },
  {
    "command": {
      "action": "splitPane",
      "split": "auto",
      "splitMode": "duplicate"
    },
    "keys": "alt+shift+d"
  },
  {
    "command": "toggleFullscreen",
    "keys": "f11"
  }
]
```

**说明：**
- `ctrl+c` 覆盖了 Windows Terminal 默认的"复制选中内容"，改为直接复制（类似普通终端体验）
- `alt+shift+d` 新建一个与当前标签页相同的分屏（复用 Profile）

### 5.3 WSL2 专属快捷键

WSL2 内部的热键由 Linux shell 决定（如 bash 使用 `Ctrl+C` 中断）。在 WSL Profile 中确保 `useSystemCursor` 为 `true`，保证 WSL 内光标跟随正常。

---

## 第六章：Oh-My-Posh + Nerd Fonts（现代提示符）

### 6.1 为什么需要

默认 PowerShell 提示符只显示当前目录，没有 git 分支、Python 虚拟环境等开发信息。Oh-My-Posh 可以显示：

```
[用户名@主机名] ~/projects/aloha (main) [⚡ py38]
$
```

- `main`：当前 git 分支
- `⚡ py38`：已激活的 Python 虚拟环境

同时，Oh-My-Posh 使用 Nerd Fonts 图标字体（如 `⚡` `⎇` `🐍`），需要安装专门的图标字体才能正常显示。

### 6.2 一站式安装 Nerd Fonts

> **2024+ 最新方案**：无需手动下载，直接使用 Nerd Fonts 官方安装脚本。

在 **PowerShell（管理员）** 中执行：

```powershell
# 下载并安装 Caskaydia Cove Nerd Font（最适合编程的等宽字体）
iwr https://github.com/ryanoasis/nerd-fonts/releases/latest/download/CascadiaCode.zip -OutFile ~\CascadiaCode.zip
Expand-Archive ~\CascadiaCode.zip -DestinationPath ~\Fonts
Get-ChildItem ~\Fonts -Filter "*.ttf" | ForEach-Object { Copy-Item $_.FullName -Destination "$env:LOCALAPPDATA\Microsoft\Windows\Fonts" }
Remove-Item ~\CascadiaCode.zip -Force
```

或者直接访问 [nerdfonts.com](https://www.nerdfonts.com/font-downloads)，下载 **Caskaydia Cove** 或 **JetBrains Mono Nerd Font**，解压后右键所有 `.ttf` 文件 → "安装"。

### 6.3 安装 Oh-My-Posh（Windows）

**方式一：winget（推荐）**

```powershell
winget install JanDeDobbeleer.OhMyPosh
```

**方式二：PowerShell Gallery**

```powershell
Install-Module oh-my-posh -Scope CurrentUser
```

### 6.4 配置 $PROFILE

```powershell
# 如果 $PROFILE 不存在，创建它
if (!(Test-Path -Path $PROFILE)) { New-Item -Type File -Path $PROFILE -Force }

# 用记事本打开
notepad $PROFILE
```

在打开的 `$PROFILE` 文件中添加：

```powershell
# 加载 Oh-My-Posh
oh-my-posh init pwsh | Invoke-Expression

# 可选：指定主题（主题文件存储在 $env:POSH_THEMES_PATH）
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/paradox.omp.json" | Invoke-Expression
```

### 6.5 推荐主题

Oh-My-Posh 内置数十套主题。查看所有主题：

```powershell
oh-my-posh theme
```

常用主题推荐：

| 主题名 | 风格 |
|--------|------|
| `paradox` | 经典 Linux 风格，彩色 git 信息 |
| `mountains-of-mars` | 深色科技风，适合暗色终端 |
| `solarized-high-sprint` | Solarized 护眼配色 |
| `jandedobbeleer` | 默认主题 |

切换主题（仅当前会话）：

```powershell
oh-my-posh theme paradox
```

永久切换主题，修改 `$PROFILE` 中的 `--config` 路径。

### 6.6 自定义主题（显示 Python 虚拟环境 + WSL 发行版）

```json
{
  "$schema": "https://github.com/JanDeDobbeleer/oh-my-posh/raw/main/themes/schema.json",
  "blocks": [
    {
      "type": "prompt",
      "alignment": "left",
      "segments": [
        {
          "type": "shell",
          "style": "diamond",
          "foreground": "#ffffff",
          "background": "#0077c2",
          "leading_diamond": "\uE0B6"
        },
        {
          "type": "path",
          "style": "powerline",
          "home": "~",
          "foreground": "#ffffff",
          "background": "#0077c2"
        },
        {
          "type": "git",
          "style": "powerline",
          "foreground": "#ffffff",
          "background": "#107c41"
        },
        {
          "type": "python",
          "style": "powerline",
          "foreground": "#ffffff",
          "background": "#af7ac5",
          "display_version": true
        },
        {
          "type": "wsl",
          "style": "powerline",
          "foreground": "#ffffff",
          "background": "#06aad5"
        },
        {
          "type": "exit",
          "style": "diamond",
          "foreground": "#ffffff",
          "background": "#c0392b",
          "trailing_diamond": "\uE0B0"
        }
      ]
    }
  ],
  "final_space": true,
  "version": 2
}
```

将上述 JSON 保存为 `~/.oh-my-posh.themes/my-custom-theme.json`，在 `$PROFILE` 中引用：

```powershell
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/my-custom-theme.json" | Invoke-Expression
```

### 6.7 在 WSL2 中安装 Oh-My-Posh（Linux 端）

如果你希望 WSL 内部和 PowerShell 保持不同的主题，可以分别在两端安装：

```bash
# 在 WSL 终端中执行
curl -s https://ohmyposh.dev/install.sh | bash -s
```

安装后，在 WSL 的 `~/.bashrc`（或 `~/.zshrc`）末尾添加：

```bash
eval "$(oh-my-posh init bash --config ~/my-custom-theme.json)"
```

---

## 第七章：Windows Terminal 与 VSCode 联动

### 7.1 将 Windows Terminal 设为 VSCode 默认终端

打开 VSCode `settings.json`（`Ctrl + Shift + P` → 输入 `settings.json`），添加：

```json
{
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.fontFamily": "CaskaydiaCove NF",
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.cursorStyle": "bar",
  "terminal.integrated.cursorBlinking": true
}
```

> `terminal.integrated.defaultProfile.windows` 的值是 Windows Terminal Profile 的 `name` 字段（如 `"PowerShell"` 或 `"Ubuntu"`）。

### 7.2 VSCode 内置 Terminal 分屏

VSCode 内置终端（`Ctrl + `` `）也支持分屏：

| 操作 | 快捷键 |
|------|--------|
| 打开终端 | `` Ctrl + ` `` |
| 分屏（水平）| `Ctrl + Shift + 5`（进入后选下半部分）|
| 分屏（垂直）| `Ctrl + Shift + 5`（进入后选左半部分）|
| 切换面板 | `Alt + ↑ ↓ ← →` |

### 7.3 从 VSCode 打开 Windows Terminal 指定目录

让 VSCode 的"在集成终端中打开"变为"在 Windows Terminal 中打开"：

```json
{
  "terminal.explorerKind": "external",
  "terminal.external.windowsExec": "wt.exe",
  "terminal.integrated.defaultLocation": "editor"
}
```

此时右键文件夹 → "在 Windows Terminal 中打开"（需配合 VSCode 插件 **"Open in Terminal"**）。

### 7.4 VSCode Remote-WSL + Windows Terminal 共用配置

**场景**：使用 VSCode Remote-WSL 插件开发，同时开 Windows Terminal 操作 WSL。

两端各自配置 Oh-My-Posh：

- Windows Terminal（PowerShell）：按第六章配置 Windows 端 `$PROFILE`
- VSCode Remote-WSL：在 WSL 内部 `.bashrc` 配置（两端提示符风格独立）

**统一效果**：两侧都用同一套 Nerd Fonts 字体（`CaskaydiaCove NF`），显示效果完全一致。

---

## 第八章：高级定制与性能优化

### 8.1 GPU 加速（默认已开启）

Windows Terminal 默认使用 GPU 渲染。如果遇到显示异常，检查 `settings.json` 中是否有：

```json
"experimental.enableGPUAnimation": true
```

### 8.2 亚克力（Acrylic）毛玻璃背景

```json
{
  "useAcrylic": true,
  "acrylicOpacity": 0.7,
  "background": "#1f1f1f"
}
```

- `useAcrylic: true`：开启亚克力模糊效果
- `acrylicOpacity: 0.7`：背景透明度（越低越透明）

> **注意**：亚克力效果在远程桌面（RDP）环境下可能不可用。

### 8.3 背景图片

```json
{
  "backgroundImage": "C:\\Users\\用户名\\Pictures\\terminal-bg.png",
  "backgroundImageOpacity": 0.3,
  "backgroundImageStretchMode": "fill"
}
```

推荐使用**低饱和度或半透明**的背景图，避免干扰终端内容。

### 8.4 WSL2 内存占用优化

WSL2 默认占用 50% 物理内存，在 Windows 端创建配置文件限制：

在 **`%USERPROFILE%\.wslconfig`**（注意：这是 Windows 文件，不是 WSL 内部文件）：

```ini
[wsl2]
memory=4GB
processors=4
swap=2GB
localhostForwarding=true
```

修改后，在 PowerShell 中执行以下命令重启 WSL：

```powershell
wsl --shutdown
```

> 再次打开 WSL 时，新配置生效。

### 8.5 禁用 WSL2 不必要的服务

在 WSL 内部编辑 `/etc/wsl.conf`（WSL 文件，不是 Windows 文件）：

```ini
[boot]
systemd=true
EOF

[network]
generateResolvConf=false
```

`generateResolvConf=false` 防止 WSL 每次启动重置 `/etc/resolv.conf`，避免自定义 DNS 配置丢失。

---

## 第九章：常用生态工具

### 9.1 Quake 模式（下沉式 Terminal）

Windows Terminal 支持类似 Quake 的下沉式唤起：用全局快捷键唤起终端，按下后终端从屏幕顶部下滑。

在 `settings.json` 的 `keybindings` 中添加：

```json
{
  "command": "toggleFullscreen",
  "keys": "win+`"
}
```

配合 `windowTransparency` 和亚克力背景，可以实现类似 macOS Spotlight 的效果。

### 9.2 Tab 标签页分组（Tab Groups）

右键标签页 → "Move to Tab Group"，将不同项目的标签页分组管理。配合 `tabColor`，可以给每个项目指定颜色标签：

```json
"tabColor": "#0078D4"
```

---

## 附录：完整 settings.json 参考配置

以下是一个包含 PowerShell 7 + Ubuntu SSH + CMD 的完整 `settings.json`，可以直接复制修改使用：

```json
{
  "$schema": "https://aka.ms/terminal-profiles-schema",
  "defaultProfile": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}",
  "copyOnSelect": false,
  "copyFormatting": false,
  "theme": "dark",
  "showTabsInTitlebar": true,
  "snapToGridOnResize": true,

  "profiles": {
    "defaults": {
      "fontFace": "CaskaydiaCove NF",
      "fontSize": 12,
      "cursorShape": "bar",
      "padding": "8, 4, 8, 4",
      "snapOnInput": true,
      "colorScheme": "One Half Dark"
    },
    "list": [
      {
        "guid": "{61c54bbd-c2c6-5271-96e7-009a87ff44bf}",
        "name": "PowerShell",
        "commandline": "powershell.exe",
        "startingDirectory": "%USERPROFILE%",
        "icon": "ms-appx:///ProfileIcons/{61c54bbd-c2c6-5271-96e7-009a87ff44bf}.png"
      },
      {
        "guid": "{7a0a52c8-1234-5678-9abc-def012345678}",
        "name": "PowerShell 7",
        "commandline": "pwsh.exe",
        "startingDirectory": "%USERPROFILE%",
        "icon": "ms-appx:///ProfileIcons/{7a0a52c8-1234-5678-9abc-def012345678}.png"
      },
      {
        "guid": "{c6eaf9f0-1234-5678-9abc-def012345679}",
        "name": "Ubuntu",
        "source": "Windows.Terminal.Wsl",
        "startingDirectory": "\\\\wsl$\\Ubuntu\\home\\用户名"
      },
      {
        "guid": "{a1b2c3d4-1234-5678-9abc-def012345680}",
        "name": "SSH - 生产服务器",
        "commandline": "ssh user@192.168.1.100",
        "tabTitle": "🚀 prod-server",
        "hidden": false
      },
      {
        "guid": "{0caa0dad-35be-5f56-a8ff-afceeeaa6101}",
        "name": "CMD",
        "commandline": "cmd.exe",
        "hidden": false
      }
    ]
  },

  "schemes": [
    {
      "name": "One Half Dark",
      "black": "#1e1e1e",
      "red": "#e06c75",
      "green": "#98c379",
      "yellow": "#e5c07b",
      "blue": "#61afef",
      "purple": "#c678dd",
      "cyan": "#56b6c2",
      "white": "#dcdfe4",
      "brightBlack": "#5c6370",
      "brightRed": "#e06c75",
      "brightGreen": "#98c379",
      "brightYellow": "#e5c07b",
      "brightBlue": "#61afef",
      "brightPurple": "#c678dd",
      "brightCyan": "#56b6c2",
      "brightWhite": "#ffffff",
      "background": "#282c34",
      "foreground": "#abb2bf"
    },
    {
      "name": "Monokai Night",
      "black": "#1f1f1f",
      "red": "#f92672",
      "green": "#a6e22e",
      "yellow": "#e6db74",
      "blue": "#6699df",
      "purple": "#ae81ff",
      "cyan": "#66d9ef",
      "white": "#f8f8f2",
      "brightBlack": "#75715e",
      "brightRed": "#f92672",
      "brightGreen": "#a6e22e",
      "brightYellow": "#e6db74",
      "brightBlue": "#6699df",
      "brightPurple": "#ae81ff",
      "brightCyan": "#66d9ef",
      "brightWhite": "#f8f8f2",
      "background": "#1f1f1f",
      "foreground": "#f8f8f2"
    }
  ],

  "keybindings": [
    {
      "command": "copy",
      "singleLine": false,
      "keys": "ctrl+c"
    },
    {
      "command": "paste",
      "keys": "ctrl+v"
    },
    {
      "command": "find",
      "keys": "ctrl+shift+f"
    },
    {
      "command": {
        "action": "splitPane",
        "split": "auto",
        "splitMode": "duplicate"
      },
      "keys": "alt+shift+d"
    },
    {
      "command": "toggleFullscreen",
      "keys": "f11"
    }
  ]
}
```

---

## 相关资源

| 资源 | 地址 |
|------|------|
| Windows Terminal 官方文档 | https://docs.microsoft.com/zh-cn/windows/terminal/ |
| Windows Terminal GitHub | https://github.com/microsoft/terminal |
| Windows Terminal Themes 预览 | https://atomcorp.github.io/themes/ |
| Nerd Fonts 下载 | https://www.nerdfonts.com/ |
| Oh-My-Posh 官网 | https://ohmyposh.dev/ |
| Oh-My-Posh 主题库 | https://ohmyposh.dev/docs/themes |
| WSL2 官方文档 | https://docs.microsoft.com/zh-cn/windows/wsl/ |
| Cascadia Code Nerd Font（微软官方）| https://github.com/microsoft/cascadia-code/releases |
