"""
测试脱敏应用的修复
"""

from advanced_desensitize_markdown import TextDesensitizer

# 测试内容
test_content = """
# 1.1 概述

该矿井深度为500米，年产量达到100万吨。
表1显示了详细数据。

## 2.1 数据分析

温度为25度，压力为150MPa。
"""

print("=" * 80)
print("测试脱敏功能")
print("=" * 80)

# 创建脱敏器
desensitizer = TextDesensitizer()

# 脱敏
print("\n原始内容:")
print(test_content)

desensitized_content = desensitizer.desensitize_content(test_content)

print("\n脱敏后内容:")
print(desensitized_content)

# 获取映射
mapping = {v: k for k, v in desensitizer.number_mapping.items()}

print("\n映射关系:")
for placeholder, original in mapping.items():
    print(f"  {placeholder} -> {original}")

print(f"\n总共替换了 {len(mapping)} 个数字")

# 测试还原
print("\n" + "=" * 80)
print("测试还原功能")
print("=" * 80)

restored_content = desensitizer.restore_content(desensitized_content, mapping)

print("\n还原后内容:")
print(restored_content)

# 验证
if restored_content == test_content:
    print("\n✅ 还原成功！内容完全一致")
else:
    print("\n❌ 还原失败！内容不一致")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

