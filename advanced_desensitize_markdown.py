import re
import json
import argparse
import os
import sys
from typing import Dict, List, Tuple
import csv


class TextDesensitizer:
    """通用文本脱敏器，支持多种文本文件格式"""
    
    def __init__(self):
        self.number_mapping = {}
        self.placeholder_counter = 1
    
    def is_section_number(self, text: str, context: str = "") -> bool:
        """判断是否为章节编号"""
        # 直接匹配章节编号模式
        # 标题中的章节编号 (# 1.1, ## 2.3.1等)
        if re.match(r'^\d+(\.\d+)+$', text.strip()):  # 至少包含一个点和两个数字部分
            # 检查上下文是否在标题中
            if re.match(r'^#{1,6}\s+' + re.escape(text.strip()), context.strip()):
                return True
            # 检查上下文是否在列表开头
            if re.match(r'^\s*' + re.escape(text.strip()) + r'\s+', context.strip()):
                return True
        elif re.match(r'^\d+$', text.strip()):  # 单独的数字
            # 检查上下文是否在标题中
            if re.match(r'^#{1,6}\s+' + re.escape(text.strip()), context.strip()):
                return True
            # 检查上下文是否在列表开头，但要排除表格行
            if re.match(r'^\s*' + re.escape(text.strip()) + r'\s+', context.strip()) and not context.strip().startswith('|'):
                return True
                
        # 附录编号 (附录A, 附录A.1)
        if re.match(r'^[附录录]{1,2}\s*[A-Z]\.?\d*(?:\.\d+)*$', text.strip()):
            return True
            
        # 表格编号 (表A.1, 表4-1-1)
        if re.match(r'^表\s*[A-Z]\.?\d+(?:\.\d+)*$', text.strip()) or re.match(r'^表\s*\d+(?:-\d+)*$', text.strip()):
            return True
            
        # 图片编号 (图A.1, 图3-2-1)
        if re.match(r'^图\s*[A-Z]\.?\d+(?:\.\d+)*$', text.strip()) or re.match(r'^图\s*\d+(?:-\d+)*$', text.strip()):
            return True
            
        # 参考文献编号 ([1] 参考文献 (#ref))
        if re.match(r'^\[\d+\]\s*.*\(#.*\)$', text.strip()):
            return True
            
        # 列表编号格式 (1), 1), 1）, (1), （1）
        # 必须至少有一个括号才算列表编号，或者是行首的数字加标点
        if re.match(r'^[\(（]\d+[\)）]$|^\d+[\)）]$', text.strip()):
            return True
            
        # 工作面/表格/图编号格式 (2-1-1, 3-2-1, 2-1)
        # 这些格式中的数字应该作为一个整体处理，不应该分开脱敏
        if re.match(r'^\d+(?:-\d+)+$', text.strip()):
            return True
            
        # 以***开始的句子中的数字（通常是标题）
        # 只有当数字本身在以***开头的行中时才排除
        if context.strip().startswith('***') and re.search(r'^\*{3}.*' + re.escape(text.strip()) + r'.*\*{3}$', context.strip()):
            return True
            
        return False
    
    def is_table_separator(self, text: str) -> bool:
        """判断是否为表格分隔符"""
        # 表格分隔符模式
        return bool(re.match(r'^\s*\|[-|\s:]+\|[-|\s:]*$', text))
        
    def is_table_data(self, text: str) -> bool:
        """判断是否为表格数据行"""
        # 表格数据行通常以|开头和结尾，且包含多个|
        return bool(re.match(r'^\s*\|.*\|\s*$', text))
    
    def extract_numbers(self, content: str) -> List[Tuple[str, int, int]]:
        """提取文本中的所有数字（排除章节编号、IP地址、邮箱、日期等）"""
        numbers = []
        
        # 先找出需要保留的内容位置（IP地址、邮箱、日期等）
        preserved_positions = []
        
        # URL中的数字
        url_pattern = r'https?://[^\s<>"]+'
        for match in re.finditer(url_pattern, content):
            preserved_positions.append((match.start(), match.end()))
            
        # 邮箱地址模式
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        for match in re.finditer(email_pattern, content):
            preserved_positions.append((match.start(), match.end()))
            
        # IPv6地址模式（更宽松的匹配）
        ipv6_pattern = r'\b(?:[0-9a-fA-F]{1,4}:)+[0-9a-fA-F]{1,4}\b'
        
        # IPv6关键词模式（不区分大小写）
        ipv6_keyword_pattern = r'[iI][pP]v6'
        for match in re.finditer(ipv6_keyword_pattern, content):
            preserved_positions.append((match.start(), match.end()))
        for match in re.finditer(ipv6_pattern, content):
            preserved_positions.append((match.start(), match.end()))
            
        # IP地址模式 (IPv4)
        ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
        for match in re.finditer(ip_pattern, content):
            preserved_positions.append((match.start(), match.end()))
            
        # 日期模式 (YYYY-MM-DD, YYYY/MM/DD, DD/MM/YYYY)
        date_patterns = [
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            r'\b\d{1,2}/\d{1,2}/\d{4}\b'
        ]
        for pattern in date_patterns:
            for match in re.finditer(pattern, content):
                preserved_positions.append((match.start(), match.end()))
                
        # 工作面/表格/图编号格式 (2-1-1, 3-2-1, 2-1, 表4-1-1, 图3-2-1)
        # 这些格式中的数字应该作为一个整体处理，不应该分开脱敏
        # 使用前瞻和后顾断言来处理中文字符边界问题
        # 匹配字母数字连字符组合，确保前后不是连字符
        workface_pattern = r'(?<!-)[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+(?!-)'
        for match in re.finditer(workface_pattern, content):
            preserved_positions.append((match.start(), match.end()))
            
        # 匹配包含字母和数字的设备编号格式 (如 设备-A-001)
        device_pattern = r'[\u4e00-\u9fa5]+-[A-Za-z0-9]+-[A-Za-z0-9]+'
        for match in re.finditer(device_pattern, content):
            preserved_positions.append((match.start(), match.end()))
        
        # 表格和图片编号格式 (表4-1-1, 图3-2-1)
        table_figure_pattern = r'(?:表|图)\s*[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+'
        for match in re.finditer(table_figure_pattern, content):
            preserved_positions.append((match.start(), match.end()))
        
        # 直接匹配所有连续的数字（整数和小数）
        # 使用更简单的模式，匹配所有数字序列
        digit_patterns = [
            r'\d+\.\d+',  # 小数
            r'\d+'  # 整数
        ]
        
        all_matches = []
        for pattern in digit_patterns:
            for match in re.finditer(pattern, content):
                number = match.group()
                start, end = match.span()
                all_matches.append((number, start, end))
                
        # 按位置排序
        all_matches.sort(key=lambda x: x[1])
        
        # 简化去重逻辑 - 只保留不重叠的匹配
        filtered_matches = []
        if all_matches:
            filtered_matches.append(all_matches[0])
            for i in range(1, len(all_matches)):
                current_match = all_matches[i]
                last_match = filtered_matches[-1]
                
                # 如果当前匹配与上一个匹配不重叠，则添加
                if current_match[1] >= last_match[2]:
                    filtered_matches.append(current_match)
                # 否则，选择更长的匹配
                elif (current_match[2] - current_match[1]) > (last_match[2] - last_match[1]):
                    filtered_matches[-1] = current_match
                    
        # 过滤掉保留区域和章节编号
        final_numbers = []
        for number, start, end in filtered_matches:
            # 检查是否在保留区域内
            is_preserved = False
            for pres_start, pres_end in preserved_positions:
                if start < pres_end and end > pres_start:
                    is_preserved = True
                    break
            
            if is_preserved:
                continue
            
            # 获取数字所在的行上下文
            line_start = content.rfind('\n', 0, start)
            if line_start == -1:
                line_start = 0
            else:
                line_start += 1
                
            line_end = content.find('\n', start)
            if line_end == -1:
                line_end = len(content)
                
            context = content[line_start:line_end]
        
            # 检查数字前后是否有括号，如果是则作为列表编号处理
            # 获取数字前后的字符
            before_char = content[start-1] if start > 0 else ''
            after_char = content[end] if end < len(content) else ''
            
            # 构造可能的列表编号格式用于检查
            possible_list_formats = []
            if before_char and after_char:
                possible_list_formats.append(before_char + number + after_char)
            if after_char:
                possible_list_formats.append(number + after_char)
            if before_char:
                possible_list_formats.append(before_char + number)
                
            # 检查是否为列表编号
            is_list_number = False
            for fmt in possible_list_formats:
                if re.match(r'^[\(（]\d+[\)）]$|^\d+[\)）]$', fmt.strip()):
                    is_list_number = True
                    break
            
            # 如果不是章节编号且不在表格分隔行中，则添加到列表中
            is_section = self.is_section_number(number, context) or is_list_number
            is_table_sep = self.is_table_separator(context)
            
            if not is_section and not is_table_sep:
                final_numbers.append((number, start, end))
                
        return final_numbers
    
    def add_to_mapping(self, number: str) -> str:
        """将数字添加到映射中，返回占位符"""
        if number not in self.number_mapping:
            placeholder = f"￥{self.placeholder_counter}￥"
            self.number_mapping[number] = placeholder
            self.placeholder_counter += 1
        return self.number_mapping[number]
    
    def desensitize_content(self, content: str) -> str:
        """对内容进行脱敏处理"""
        # 提取所有数字
        numbers = self.extract_numbers(content)
        
        # 按位置从后往前排序，避免位置偏移
        numbers.sort(key=lambda x: x[1], reverse=True)
        
        # 执行替换
        result = content
        for number, start, end in numbers:
            placeholder = self.add_to_mapping(number)
            result = result[:start] + placeholder + result[end:]
            
        return result
    
    def save_mapping(self, mapping_file_path: str):
        """保存映射关系到JSON文件"""
        # 创建反向映射（占位符->原始数字）
        reverse_mapping = {v: k for k, v in self.number_mapping.items()}
        
        with open(mapping_file_path, 'w', encoding='utf-8') as f:
            json.dump(reverse_mapping, f, ensure_ascii=False, indent=2)
            
    def load_mapping(self, mapping_file_path: str) -> Dict[str, str]:
        """从JSON文件加载映射关系"""
        if not os.path.exists(mapping_file_path):
            return {}
            
        with open(mapping_file_path, 'r', encoding='utf-8') as f:
            reverse_mapping = json.load(f)
            
        # 返回原始的反向映射（占位符->原始数字），用于还原
        return reverse_mapping
        
    def restore_content(self, content: str, mapping: Dict[str, str]) -> str:
        """根据映射关系还原内容"""
        result = content
        
        for placeholder, number in mapping.items():
            result = result.replace(placeholder, number)
        
        return result


def desensitize_text_file(file_path: str, output_path=None):
    """对通用文本文件进行脱敏处理"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在")
        
    if output_path is None:
        base_name = os.path.splitext(file_path)[0]
        ext = os.path.splitext(file_path)[1]
        output_path = f"{base_name}_desensitized{ext}"
        
    # 生成映射文件路径
    mapping_file_path = f"{os.path.splitext(output_path)[0]}_map.json"

    # 创建脱敏器实例
    desensitizer = TextDesensitizer()
    
    # 读取文件内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()

    # 执行脱敏
    desensitized_content = desensitizer.desensitize_content(content)
    
    # 保存脱敏后的内容
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(desensitized_content)
        
    # 保存映射关系
    desensitizer.save_mapping(mapping_file_path)
    
    print(f"脱敏完成！")
    print(f"结果已保存至: {output_path}")
    print(f"映射关系已保存至: {mapping_file_path}")
    print(f"共脱敏 {len(desensitizer.number_mapping)} 个数字")


def restore_text_file(file_path: str, mapping_file_path: str, output_path=None):
    """根据映射文件还原文本文件"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"文件 {file_path} 不存在")
        
    if not os.path.exists(mapping_file_path):
        raise FileNotFoundError(f"映射文件 {mapping_file_path} 不存在")
        
    if output_path is None:
        base_name = os.path.splitext(file_path)[0]
        ext = os.path.splitext(file_path)[1]
        output_path = f"{base_name}_restored{ext}"

    # 创建脱敏器实例
    desensitizer = TextDesensitizer()
    
    # 加载映射关系
    mapping = desensitizer.load_mapping(mapping_file_path)
    
    # 读取脱敏后的内容
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        # 尝试其他编码
        with open(file_path, 'r', encoding='gbk') as f:
            content = f.read()

    # 执行还原
    restored_content = desensitizer.restore_content(content, mapping)
    
    # 保存还原后的内容
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(restored_content)
        
    print(f"还原完成！")
    print(f"结果已保存至: {output_path}")


def process_directory(input_dir: str, output_dir=None):
    """处理目录中的所有文本文件"""
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"目录 {input_dir} 不存在")
        
    if output_dir is None:
        output_dir = f"{input_dir}_desensitized"
        
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 遍历目录中的所有文本文件
    processed_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.md', '.txt', '.csv', '.json', '.xml', '.html', '.htm', '.py', '.js', '.ts', '.css', '.sql', '.log')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            try:
                desensitize_text_file(input_path, output_path)
                processed_count += 1
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")

    print(f"已完成 {processed_count} 个文件的脱敏处理")


def process_directory_restore(input_dir: str, mapping_file_path: str, output_dir=None):
    """使用映射文件还原目录中的所有文本文件"""
    if not os.path.exists(input_dir):
        raise FileNotFoundError(f"目录 {input_dir} 不存在")
    
    if not os.path.exists(mapping_file_path):
        raise FileNotFoundError(f"映射文件 {mapping_file_path} 不存在")
    
    if output_dir is None:
        output_dir = f"{input_dir}_restored"
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载映射关系
    desensitizer = TextDesensitizer()
    mapping = desensitizer.load_mapping(mapping_file_path)
    
    # 遍历目录中的所有文本文件
    processed_count = 0
    for filename in os.listdir(input_dir):
        if filename.lower().endswith(('.md', '.txt', '.csv', '.json', '.xml', '.html', '.htm', '.py', '.js', '.ts', '.css', '.sql', '.log')):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, filename)
            
            try:
                # 读取脱敏后的内容
                try:
                    with open(input_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    # 尝试其他编码
                    with open(input_path, 'r', encoding='gbk') as f:
                        content = f.read()
                
                # 执行还原
                restored_content = desensitizer.restore_content(content, mapping)
                
                # 保存还原后的内容
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(restored_content)
                
                processed_count += 1
                print(f"已还原文件: {filename}")
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
    
    print(f"已完成 {processed_count} 个文件的还原处理，使用映射文件: {mapping_file_path}")


def main():
    parser = argparse.ArgumentParser(description='对文本文件进行数字脱敏处理')
    parser.add_argument('input', help='输入文件或目录路径')
    parser.add_argument('-o', '--output', help='输出文件或目录路径')
    parser.add_argument('-r', '--restore', action='store_true', help='还原模式（需要提供映射文件）')
    parser.add_argument('-m', '--mapping', help='映射文件路径（用于还原模式）')
    
    args = parser.parse_args()
    
    if args.restore:
        # 还原模式
        if not args.mapping:
            print("错误：还原模式需要指定映射文件 (-m)")
            sys.exit(1)
        
        if os.path.isfile(args.input):
            # 还原单个文件
            restore_text_file(args.input, args.mapping, args.output)
        elif os.path.isdir(args.input):
            # 还原整个目录
            process_directory_restore(args.input, args.mapping, args.output)
        else:
            print("错误：输入路径既不是文件也不是目录")
            sys.exit(1)
    elif os.path.isfile(args.input):
        # 处理单个文件
        desensitize_text_file(args.input, args.output)
    elif os.path.isdir(args.input):
        # 处理整个目录
        process_directory(args.input, args.output)
    else:
        print("错误：输入路径既不是文件也不是目录")
        sys.exit(1)


if __name__ == "__main__":
    main()