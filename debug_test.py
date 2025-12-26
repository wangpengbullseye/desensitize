import re

content = '其他编号包括：A1-B2-3、XY-9-10、Test-1-2、AB-CD-EF-1等。'

# 检查工作面模式
workface_pattern = r'\b[A-Za-z0-9]+(?:-[A-Za-z0-9]+)+\b'
matches = re.findall(workface_pattern, content)
print('工作面模式匹配:', matches)

# 检查具体部分
part = 'AB-CD-EF-1'
match = re.search(workface_pattern, part)
print(f'AB-CD-EF-1是否匹配:', match is not None)
if match:
    print(f'匹配结果: {match.group()}, 位置: {match.start()}-{match.end()}')

# 检查边界问题
print()
print('检查边界情况:')
test_cases = [
    'AB-CD-EF-1等。',
    'AB-CD-EF-1',
    ' AB-CD-EF-1 ',
    '包含AB-CD-EF-1等'
]

for case in test_cases:
    match = re.search(workface_pattern, case)
    print(f'"{case}" -> {match.group() if match else "无匹配"}')
    
# 检查更复杂的情况
print()
print('更详细的分析:')
full_text = '其他编号包括：A1-B2-3、XY-9-10、Test-1-2、AB-CD-EF-1等。'
for match in re.finditer(workface_pattern, full_text):
    print(f'匹配: "{match.group()}", 位置: {match.start()}-{match.end()}')
    
# 检查为什么AB-CD-EF-1没被匹配
print()
print('分析"AB-CD-EF-1等。"部分:')
part_with_context = 'AB-CD-EF-1等。'
for match in re.finditer(workface_pattern, part_with_context):
    print(f'匹配: "{match.group()}", 位置: {match.start()}-{match.end()}')
    
# 问题可能在于\b边界 - "1等"中"1"后面不是单词边界
print()
print('分析边界问题:')
test = '1等'
# \b要求一边是单词字符，一边是非单词字符
# '1'后面是'等'(中文字符，也被视为单词字符)，所以\b不匹配
print('re.match(r"\\\\b1\\\\b", "1等"):', bool(re.match(r'\b1\b', '1等')))
print('re.match(r"\\\\b1$", "1等"):', bool(re.match(r'\b1', '1等')))