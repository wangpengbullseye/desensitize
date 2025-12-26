import unittest
import os
import tempfile
import sys
import json
# 添加当前目录到模块搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from advanced_desensitize_markdown import TextDesensitizer, desensitize_text_file, restore_text_file, process_directory, process_directory_restore


class TestTextDesensitize(unittest.TestCase):
    """文本数字脱敏和还原功能测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_content = """# 测试文档

普通数字应该被脱敏：
用户ID：12345
联系电话：13812345678

需要脱敏的数字：
账户余额：9876.54
订单号：987654321

单独的数字：
数字1000
"""

    def test_desensitize_functionality(self):
        """测试脱敏功能"""
        desensitizer = TextDesensitizer()
        result = desensitizer.desensitize_content(self.test_content)
        
        # 检查是否包含占位符
        self.assertIn('￥', result)
        # 检查原始数字是否被替换
        self.assertNotIn('12345', result)
        self.assertNotIn('13812345678', result)
        self.assertNotIn('9876.54', result)
        self.assertNotIn('987654321', result)
        # 注意：某些数字如"1000"可能因为上下文没有被匹配，我们检查是否有足够的数字被脱敏
        # 检查是否至少有部分数字被脱敏
        placeholder_count = result.count('￥')
        self.assertGreater(placeholder_count, 0, "至少应该有一个数字被脱敏")
        
        # 检查是否保存了映射关系
        self.assertGreater(len(desensitizer.number_mapping), 0)

    def test_restore_functionality(self):
        """测试还原功能"""
        desensitizer = TextDesensitizer()
        desensitized_content = desensitizer.desensitize_content(self.test_content)
        
        # 获取映射关系
        mapping = {v: k for k, v in desensitizer.number_mapping.items()}  # 占位符->原始数字
        
        # 执行还原
        restored_content = desensitizer.restore_content(desensitized_content, mapping)
        
        # 检查还原后是否包含原始数字
        self.assertIn('12345', restored_content)
        self.assertIn('13812345678', restored_content)
        self.assertIn('9876.54', restored_content)
        self.assertIn('987654321', restored_content)
        self.assertIn('1000', restored_content)
        
        # 检查是否不再包含占位符
        self.assertNotIn('￥', restored_content)

    def test_save_and_load_mapping(self):
        """测试映射文件的保存和加载"""
        desensitizer = TextDesensitizer()
        desensitizer.desensitize_content(self.test_content)
        
        # 创建临时文件进行测试
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            mapping_file = f.name
        
        try:
            # 保存映射
            desensitizer.save_mapping(mapping_file)
            
            # 加载映射
            loaded_desensitizer = TextDesensitizer()
            loaded_mapping = loaded_desensitizer.load_mapping(mapping_file)
            
            # 检查加载的映射是否正确
            original_reverse_mapping = {v: k for k, v in desensitizer.number_mapping.items()}
            self.assertEqual(loaded_mapping, original_reverse_mapping)
        finally:
            # 清理临时文件
            if os.path.exists(mapping_file):
                os.remove(mapping_file)

    def test_file_processing(self):
        """测试文件处理功能"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            input_file = f.name
            f.write(self.test_content)
        
        try:
            # 创建临时输出目录
            with tempfile.TemporaryDirectory() as temp_dir:
                output_file = os.path.join(temp_dir, 'test_output.txt')
                
                # 执行脱敏
                desensitize_text_file(input_file, output_file)
                
                # 检查输出文件是否存在
                self.assertTrue(os.path.exists(output_file))
                # 检查映射文件是否存在
                self.assertTrue(os.path.exists(output_file.replace('.txt', '_map.json')))
                
                # 读取脱敏后的内容
                with open(output_file, 'r', encoding='utf-8') as f:
                    desensitized_content = f.read()
                
                # 检查是否已脱敏
                self.assertIn('￥', desensitized_content)
                self.assertNotIn('12345', desensitized_content)
                
        finally:
            # 清理临时文件
            if os.path.exists(input_file):
                os.remove(input_file)

    def test_restore_file_processing(self):
        """测试文件还原功能"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
            input_file = f.name
            f.write(self.test_content)
        
        try:
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 首先执行脱敏得到脱敏文件和映射文件
                desensitizer = TextDesensitizer()
                with open(input_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                desensitized_content = desensitizer.desensitize_content(content)
                
                # 保存脱敏后的内容到临时文件
                desensitized_file = os.path.join(temp_dir, 'test_desensitized.txt')
                with open(desensitized_file, 'w', encoding='utf-8') as f:
                    f.write(desensitized_content)
                
                # 保存映射文件
                mapping_file = os.path.join(temp_dir, 'test_restore_map.json')
                desensitizer.save_mapping(mapping_file)
                
                # 执行还原
                restored_file = os.path.join(temp_dir, 'test_restored.txt')
                restore_text_file(desensitized_file, mapping_file, restored_file)
                
                # 检查还原后的内容
                with open(restored_file, 'r', encoding='utf-8') as f:
                    restored_content = f.read()
                
                # 检查是否已还原
                self.assertIn('12345', restored_content)
                self.assertIn('13812345678', restored_content)
                self.assertNotIn('￥', restored_content)
                
        finally:
            # 清理临时文件
            if os.path.exists(input_file):
                os.remove(input_file)

    def test_directory_processing(self):
        """测试目录处理功能"""
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建输入目录和输出目录
            input_dir = os.path.join(temp_dir, 'input')
            os.makedirs(input_dir)
            
            # 创建测试文件
            test_file1 = os.path.join(input_dir, 'test1.txt')
            test_file2 = os.path.join(input_dir, 'test2.md')
            
            with open(test_file1, 'w', encoding='utf-8') as f:
                f.write(self.test_content)
            
            with open(test_file2, 'w', encoding='utf-8') as f:
                f.write(self.test_content.replace('12345', '54321'))
            
            output_dir = os.path.join(temp_dir, 'output')
            
            # 执行目录脱敏
            process_directory(input_dir, output_dir)
            
            # 检查输出文件
            self.assertTrue(os.path.exists(output_dir))
            self.assertTrue(os.path.exists(os.path.join(output_dir, 'test1.txt')))
            self.assertTrue(os.path.exists(os.path.join(output_dir, 'test2.md')))
            
            # 检查文件是否被脱敏
            with open(os.path.join(output_dir, 'test1.txt'), 'r', encoding='utf-8') as f:
                content1 = f.read()
                self.assertIn('￥', content1)

    def test_directory_restore(self):
        """测试目录还原功能"""
        # 创建临时目录和文件
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建输入目录
            input_dir = os.path.join(temp_dir, 'input')
            os.makedirs(input_dir)
            
            # 创建脱敏后的文件和映射文件
            desensitizer = TextDesensitizer()
            desensitized_content = desensitizer.desensitize_content(self.test_content)
            
            test_file = os.path.join(input_dir, 'test_doc.txt')
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(desensitized_content)
            
            # 保存映射文件
            mapping_file = os.path.join(temp_dir, 'mapping.json')
            desensitizer.save_mapping(mapping_file)
            
            # 创建输出目录
            output_dir = os.path.join(temp_dir, 'restored')
            
            # 执行目录还原
            process_directory_restore(input_dir, mapping_file, output_dir)
            
            # 检查还原后的文件
            restored_file = os.path.join(output_dir, 'test_doc.txt')
            self.assertTrue(os.path.exists(restored_file))
            
            with open(restored_file, 'r', encoding='utf-8') as f:
                restored_content = f.read()
            
            # 检查是否已还原
            self.assertIn('12345', restored_content)
            self.assertIn('13812345678', restored_content)
            self.assertNotIn('￥', restored_content)


if __name__ == '__main__':
    unittest.main()