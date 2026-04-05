# 加载 Oh-My-Posh
#oh-my-posh init pwsh | Invoke-Expression

# 可选：指定主题（主题文件存储在 $env:POSH_THEMES_PATH）
# oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/paradox.omp.json" | Invoke-Expression
#oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH/my-python-wsl.json" | Invoke-Expression

# 设置主题路径（注意用你自己的用户名）
$env:POSH_THEMES_PATH = "C:\Users\linbirg\.oh-my-posh\themes"
# 初始化 oh-my-posh（使用 paradox 主题）
oh-my-posh init pwsh --config "$env:POSH_THEMES_PATH\my-python-wsl.json" | Invoke-Expression

#插件导入
Import-Module posh-git

Import-Module oh-my-posh

Import-Module PSReadLine

#快捷键设置

# 设置预测文本来源为历史记录
Set-PSReadLineOption -PredictionSource History

# 每次回溯输入历史，光标定位于输入内容末尾
Set-PSReadLineOption -HistorySearchCursorMovesToEnd

# 设置 Tab 为菜单补全和 Intellisense
Set-PSReadLineKeyHandler -Key "Tab" -Function MenuComplete

# 设置 Ctrl+d 为退出 PowerShell
Set-PSReadlineKeyHandler -Key "Ctrl+d" -Function ViExit

# 设置 Ctrl+z 为撤销
Set-PSReadLineKeyHandler -Key "Ctrl+z" -Function Undo

# 设置向上键为后向搜索历史记录
Set-PSReadLineKeyHandler -Key UpArrow -Function HistorySearchBackward

# 设置向下键为前向搜索历史纪录
Set-PSReadLineKeyHandler -Key DownArrow -Function HistorySearchForward