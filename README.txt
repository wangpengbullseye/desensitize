Markdown数字脱敏工具使用说明
=========================

功能介绍：
1. 数字脱敏：将文本文件中的敏感数字替换为占位符
2. 数字还原：使用映射文件将占位符还原为原始数字
3. 支持多种文本文件格式（Markdown、CSV、JSON、TXT、XML、HTML、Python、JavaScript等）
4. 支持单文件和目录批量处理
5. 支持使用单个映射文件还原多个不同名称的文件

使用方法：
1. 运行 run_gui.bat 启动图形界面
2. 或直接运行：python gui_desensitize.py

命令行使用（高级用户）：
- 脱敏：python advanced_desensitize_markdown.py <input_file>
- 还原：python advanced_desensitize_markdown.py -r -m <mapping_file> <desensitized_file>

支持的文件格式：
- .md (Markdown文件)
- .txt (文本文件)
- .csv (CSV文件)
- .json (JSON文件)
- .xml (XML文件)
- .html/.htm (HTML文件)
- .py (Python文件)
- .js/.ts (JavaScript/TypeScript文件)
- .css (CSS文件)
- .sql (SQL文件)
- .log (日志文件)

界面说明：
- 脱敏模式：将敏感数字替换为占位符
- 还原模式：使用映射文件还原原始数字
- 支持选择单个文件或整个目录
- 映射文件在脱敏时自动生成，还原时需要指定