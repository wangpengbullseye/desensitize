import unittest
import os
import tempfile
import sys
# 添加当前目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_desensitize_markdown import TextDesensitizer, desensitize_text_file, restore_text_file, process_directory, process_directory_restore


class TestIntegration(unittest.TestCase):
    """集成测试，使用真实的测试文件"""
    
    def setUp(self):
        """测试前准备"""
        # 获取测试文件路径
        self.test_file_path = os.path.join(os.path.dirname(__file__), 'test_exclusions.md')
        
        if not os.path.exists(self.test_file_path):
            # 如果测试文件不存在，创建一个简单的测试文件
            with open(self.test_file_path, 'w', encoding='utf-8') as f:
                f.write("""# 测试排除规则

1) 这是一个列表项
2）这也是一个列表项
(3) 圆括号列表项
（4）中文圆括号列表项

普通数字应该被脱敏：
用户ID：12345
联系电话：13812345678

需要脱敏的数字：
账户余额：9876.54
订单号：987654321

单独的数字：
数字1000
""")

    def test_end_to_end_desensitize_and_restore(self):
        """端到端测试：脱敏后还原"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 定义文件路径
            input_file = os.path.join(temp_dir, 'input.txt')
            desensitized_file = os.path.join(temp_dir, 'output_desensitized.txt')
            restored_file = os.path.join(temp_dir, 'output_restored.txt')
            
            # 复制原始文件到临时目录
            with open(self.test_file_path, 'r', encoding='utf-8') as src:
                original_content = src.read()
            
            with open(input_file, 'w', encoding='utf-8') as dst:
                dst.write(original_content)
            
            # 执行脱敏
            desensitize_text_file(input_file, desensitized_file)
            
            # 检查脱敏文件是否创建
            self.assertTrue(os.path.exists(desensitized_file))
            
            # 检查映射文件是否创建
            expected_mapping_file = desensitized_file.replace('_desensitized.txt', '_map.json')
            if not os.path.exists(expected_mapping_file):
                # 如果上面的替换不正确，尝试另一种方式
                expected_mapping_file = os.path.join(temp_dir, 'output_desensitized_map.json')
            
            if not os.path.exists(expected_mapping_file):
                # 查找可能的映射文件名
                for file in os.listdir(temp_dir):
                    if file.endswith('_desensitized_map.json'):
                        expected_mapping_file = os.path.join(temp_dir, file)
                        break
            
            if not os.path.exists(expected_mapping_file):
                # 再次查找
                for file in os.listdir(temp_dir):
                    if file.endswith('_map.json') and 'desensitized' in file:
                        expected_mapping_file = os.path.join(temp_dir, file)
                        break
            
            self.assertTrue(os.path.exists(expected_mapping_file), 
                          f"映射文件不存在: {expected_mapping_file}")
            
            # 执行还原
            restore_text_file(desensitized_file, expected_mapping_file, restored_file)
            
            # 检查还原文件是否创建
            self.assertTrue(os.path.exists(restored_file))
            
            # 读取还原后的内容
            with open(restored_file, 'r', encoding='utf-8') as f:
                restored_content = f.read()
            
            # 验证还原后的内容与原始内容相似（数字应该还原，但格式可能略有不同）
            # 检查关键数字是否还原
            self.assertIn('12345', restored_content)
            self.assertIn('13812345678', restored_content)
            self.assertIn('9876.54', restored_content)
            self.assertIn('987654321', restored_content)
            self.assertIn('1000', restored_content)
            
            # 确保还原后的内容不包含占位符
            self.assertNotIn('￥', restored_content)

    def test_multiple_files_directory_processing(self):
        """测试多文件目录处理 - 验证单个映射文件还原多个文件的功能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建脱敏后的文件和映射文件（模拟使用单个映射文件处理多个文件的场景）
            input_dir = os.path.join(temp_dir, 'desensitized_files')
            output_dir = os.path.join(temp_dir, 'restored_files')
            
            os.makedirs(input_dir)
            
            # 首先创建一个脱敏器和映射关系
            desensitizer = TextDesensitizer()
            original_content = """# 测试文档

用户ID：12345
联系电话：13812345678
账户余额：9876.54
订单号：987654321
数字：1000
"""
            # 对内容进行脱敏以生成映射
            desensitized_content = desensitizer.desensitize_content(original_content)
            
            # 保存映射文件
            mapping_file = os.path.join(temp_dir, 'shared_mapping.json')
            desensitizer.save_mapping(mapping_file)
            
            # 创建多个相同的脱敏文件（模拟多个不同名称但内容结构相似的文件）
            for i in range(3):
                filename = f'document_{i+1}.txt'
                file_path = os.path.join(input_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(desensitized_content)  # 使用相同的脱敏内容
            
            # 创建输出目录
            os.makedirs(output_dir)
            
            # 使用单个映射文件还原所有文件
            process_directory_restore(input_dir, mapping_file, output_dir)
            
            # 验证所有文件都被正确还原
            for i in range(3):
                restored_file = os.path.join(output_dir, f'document_{i+1}.txt')
                self.assertTrue(os.path.exists(restored_file))
                
                # 检查文件是否被正确还原
                with open(restored_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 检查原始数字是否还原
                    self.assertIn('12345', content)
                    self.assertIn('13812345678', content)
                    self.assertIn('9876.54', content)
                    self.assertIn('987654321', content)
                    self.assertIn('1000', content)
                    # 确保没有占位符
                    self.assertNotIn('￥', content)

    def test_single_mapping_multiple_files_with_different_formats(self):
        """测试使用单个映射文件还原多种格式的文件"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建脱敏后的多种格式文件和映射文件
            input_dir = os.path.join(temp_dir, 'desensitized_files')
            output_dir = os.path.join(temp_dir, 'restored_files')
            
            os.makedirs(input_dir)
            
            # 首先创建一个脱敏器和映射关系
            desensitizer = TextDesensitizer()
            original_content = """姓名,年龄,电话号码,工资
张三,25,13812345678,8500.50
李四,30,13987654321,9200.75
"""
            # 对内容进行脱敏以生成映射
            desensitized_content = desensitizer.desensitize_content(original_content)
            
            # 保存映射文件
            mapping_file = os.path.join(temp_dir, 'csv_mapping.json')
            desensitizer.save_mapping(mapping_file)
            
            # 创建多种格式的脱敏文件
            formats = ['.txt', '.csv', '.md', '.json']
            for i, fmt in enumerate(formats):
                filename = f'data_{i+1}{fmt}'
                file_path = os.path.join(input_dir, filename)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(desensitized_content)  # 使用相同的脱敏内容
            
            # 创建输出目录
            os.makedirs(output_dir)
            
            # 使用单个映射文件还原所有文件
            process_directory_restore(input_dir, mapping_file, output_dir)
            
            # 验证所有文件都被正确还原
            for i, fmt in enumerate(formats):
                restored_file = os.path.join(output_dir, f'data_{i+1}{fmt}')
                self.assertTrue(os.path.exists(restored_file))
                
                # 检查文件是否被正确还原
                with open(restored_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 检查原始数字是否还原
                    self.assertIn('25', content)
                    self.assertIn('13812345678', content)
                    self.assertIn('8500.50', content)
                    self.assertIn('30', content)
                    self.assertIn('13987654321', content)
                    self.assertIn('9200.75', content)
                    # 确保没有占位符
                    self.assertNotIn('￥', content)

    def test_exclusion_patterns_preservation(self):
        """测试排除模式的保护 - 确保煤层号、图号、表号等不被脱敏"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, 'exclusion_test.txt')
            output_file = os.path.join(temp_dir, 'exclusion_test_desensitized.txt')
            
            # 测试内容包含需要保护的模式
            test_content = """距下部 3-1 煤层间距 27.19～37.43m，平均 30.85m。

图 4-1-1 显示了相关数据，表 4-1-1 中列出了详细信息。

3-1 煤层的平均厚度为 5.2m，开采深度在 1200～1300m 之间。

其他数据包括：温度 25.5℃，压力 3.2MPa，流量 150.8m³/h。"""
            
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 执行脱敏
            desensitize_text_file(input_file, output_file)
            
            # 读取脱敏后的内容
            with open(output_file, 'r', encoding='utf-8') as f:
                desensitized_content = f.read()
            
            # 验证保护的模式仍然存在
            self.assertIn('3-1 煤层', desensitized_content)  # 煤层号应该保留
            self.assertIn('图 4-1-1', desensitized_content)   # 图号应该保留
            self.assertIn('表 4-1-1', desensitized_content)   # 表号应该保留
            
            # 验证敏感数字被脱敏
            self.assertIn('￥', desensitized_content)  # 应该有占位符
            self.assertNotIn('27.19', desensitized_content)  # 敏感小数应该被脱敏
            self.assertNotIn('37.43', desensitized_content)  # 敏感小数应该被脱敏
            self.assertNotIn('30.85', desensitized_content)  # 敏感小数应该被脱敏
            self.assertNotIn('1200', desensitized_content)   # 敏感整数应该被脱敏
            self.assertNotIn('1300', desensitized_content)   # 敏感整数应该被脱敏
            self.assertNotIn('25.5', desensitized_content)   # 敏感小数应该被脱敏
            self.assertNotIn('3.2', desensitized_content)    # 敏感小数应该被脱敏
            self.assertNotIn('150.8', desensitized_content)  # 敏感小数应该被脱敏
            
            # 检查映射文件
            # 修正映射文件路径的构建
            expected_mapping_file = os.path.join(temp_dir, 'exclusion_test_desensitized_map.json')
            if not os.path.exists(expected_mapping_file):
                # 查找可能的映射文件
                for file in os.listdir(temp_dir):
                    if file.endswith('_desensitized_map.json'):
                        expected_mapping_file = os.path.join(temp_dir, file)
                        break
            
            self.assertTrue(os.path.exists(expected_mapping_file), 
                          f"映射文件不存在: {expected_mapping_file}")
            
            # 还原测试
            restored_file = os.path.join(temp_dir, 'exclusion_test_restored.txt')
            restore_text_file(output_file, expected_mapping_file, restored_file)
            
            # 读取还原后的内容
            with open(restored_file, 'r', encoding='utf-8') as f:
                restored_content = f.read()
            
            # 验证还原后的内容
            self.assertIn('3-1 煤层', restored_content)  # 煤层号应该保留
            self.assertIn('图 4-1-1', restored_content)   # 图号应该保留
            self.assertIn('表 4-1-1', restored_content)   # 表号应该保留
            self.assertIn('27.19', restored_content)     # 敏感数字应该还原
            self.assertIn('37.43', restored_content)     # 敏感数字应该还原
            self.assertIn('30.85', restored_content)     # 敏感数字应该还原
            self.assertIn('1200', restored_content)      # 敏感数字应该还原
            self.assertIn('1300', restored_content)      # 敏感数字应该还原
            self.assertIn('25.5', restored_content)      # 敏感数字应该还原
            self.assertIn('3.2', restored_content)       # 敏感数字应该还原
            self.assertIn('150.8', restored_content)     # 敏感数字应该还原
            self.assertNotIn('￥', restored_content)     # 不应该有占位符

    def test_complex_numbering_patterns_preservation(self):
        """测试复杂编号模式的保护 - 确保字母数字组合编号不被脱敏"""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = os.path.join(temp_dir, 'complex_numbering_test.txt')
            output_file = os.path.join(temp_dir, 'complex_numbering_test_desensitized.txt')
            
            # 测试内容包含复杂编号模式
            test_content = """钻孔编号：43-DZ-1 至 43-DZ-8

其他编号包括：A1-B2-3、XY-9-10、Test-1-2、AB-CD-EF-1等。

系统参数：温度25.5℃，压力3.2MPa，流量150.8m³/h。

设备编号：设备-A-001、机器-B-002、装置-C-003。

特殊编号：43-DZ-1 编至 43-DZ-8，A-1-1 至 A-1-10。"""
            
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 执行脱敏
            desensitize_text_file(input_file, output_file)
            
            # 读取脱敏后的内容
            with open(output_file, 'r', encoding='utf-8') as f:
                desensitized_content = f.read()
            
            # 验证保护的编号模式仍然存在
            self.assertIn('43-DZ-1', desensitized_content)  # 复杂编号应该保留
            self.assertIn('43-DZ-8', desensitized_content)  # 复杂编号应该保留
            self.assertIn('A1-B2-3', desensitized_content)  # 字母数字组合编号应该保留
            self.assertIn('XY-9-10', desensitized_content)  # 字母数字组合编号应该保留
            self.assertIn('Test-1-2', desensitized_content)  # 字母数字组合编号应该保留
            self.assertIn('AB-CD-EF-1', desensitized_content)  # 字母数字组合编号应该保留
            self.assertIn('设备-A-001', desensitized_content)  # 设备编号应该保留
            self.assertIn('机器-B-002', desensitized_content)  # 设备编号应该保留
            self.assertIn('装置-C-003', desensitized_content)  # 设备编号应该保留
            
            # 验证敏感数字被脱敏
            self.assertIn('￥', desensitized_content)  # 应该有占位符
            self.assertNotIn('25.5', desensitized_content)  # 敏感小数应该被脱敏
            self.assertNotIn('3.2', desensitized_content)   # 敏感小数应该被脱敏
            self.assertNotIn('150.8', desensitized_content)  # 敏感小数应该被脱敏
            
            # 检查映射文件
            expected_mapping_file = os.path.join(temp_dir, 'complex_numbering_test_desensitized_map.json')
            self.assertTrue(os.path.exists(expected_mapping_file), 
                          f"映射文件不存在: {expected_mapping_file}")
            
            # 还原测试
            restored_file = os.path.join(temp_dir, 'complex_numbering_test_restored.txt')
            restore_text_file(output_file, expected_mapping_file, restored_file)
            
            # 读取还原后的内容
            with open(restored_file, 'r', encoding='utf-8') as f:
                restored_content = f.read()
            
            # 验证还原后的内容
            self.assertIn('43-DZ-1', restored_content)  # 复杂编号应该保留
            self.assertIn('43-DZ-8', restored_content)  # 复杂编号应该保留
            self.assertIn('A1-B2-3', restored_content)  # 字母数字组合编号应该保留
            self.assertIn('XY-9-10', restored_content)  # 字母数字组合编号应该保留
            self.assertIn('Test-1-2', restored_content)  # 字母数字组合编号应该保留
            self.assertIn('AB-CD-EF-1', restored_content)  # 字母数字组合编号应该保留
            self.assertIn('设备-A-001', restored_content)  # 设备编号应该保留
            self.assertIn('机器-B-002', restored_content)  # 设备编号应该保留
            self.assertIn('装置-C-003', restored_content)  # 设备编号应该保留
            self.assertIn('25.5', restored_content)      # 敏感数字应该还原
            self.assertIn('3.2', restored_content)       # 敏感数字应该还原
            self.assertIn('150.8', restored_content)     # 敏感数字应该还原
            self.assertNotIn('￥', restored_content)     # 不应该有占位符


if __name__ == '__main__':
    unittest.main()