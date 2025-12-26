"""
数据脱敏工具 Web应用
基于Streamlit构建的文本数据脱敏和还原工具

版本: 1.0.0
"""

import streamlit as st
import json
import zipfile
from io import BytesIO
from pathlib import Path
import sys

# 添加当前目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from advanced_desensitize_markdown import TextDesensitizer

# 页面配置
st.set_page_config(
    page_title="数据脱敏工具",
    page_icon="🔒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("🔒 数据脱敏工具")
st.markdown("**对文本文件中的敏感数字进行脱敏处理，支持还原**")

# 侧边栏
with st.sidebar:
    st.header("📋 功能说明")
    st.markdown("""
    ### 脱敏功能：
    - 自动识别并替换敏感数字
    - 保留章节编号、表格编号等
    - 生成映射文件用于还原
    
    ### 还原功能：
    - 使用映射文件还原原始数据
    - 支持批量还原
    
    ### 支持格式：
    - Markdown (.md)
    - 文本文件 (.txt)
    - CSV (.csv)
    - JSON (.json)
    - 其他文本格式
    """)
    
    st.divider()
    st.markdown("**版本**: 1.0.0")

# 主界面
tab1, tab2, tab3 = st.tabs(["🔒 数据脱敏", "🔓 数据还原", "📖 帮助"])

# Tab 1: 数据脱敏
with tab1:
    st.header("数据脱敏")
    
    st.info("上传文件后，系统会自动识别并替换敏感数字，生成脱敏文件和映射文件")
    
    # 文件上传
    uploaded_files = st.file_uploader(
        "选择要脱敏的文件（可多选）",
        type=['md', 'txt', 'csv', 'json', 'xml', 'html', 'py', 'js'],
        accept_multiple_files=True,
        key="desensitize_files"
    )
    
    if uploaded_files:
        st.success(f"已上传 {len(uploaded_files)} 个文件")
        
        # 显示文件列表
        with st.expander("查看上传的文件"):
            for file in uploaded_files:
                st.text(f"📄 {file.name}")
    
    # 脱敏按钮
    if st.button("🔒 开始脱敏", type="primary", disabled=not uploaded_files):
        with st.spinner("正在脱敏..."):
            try:
                results = []

                # 处理每个文件（每个文件使用独立的desensitizer）
                for file in uploaded_files:
                    # 为每个文件创建新的desensitizer实例
                    desensitizer = TextDesensitizer()

                    # 读取文件内容
                    try:
                        content = file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        content = file.read().decode('gbk')

                    # 脱敏
                    desensitized_content = desensitizer.desensitize_content(content)

                    # 获取映射关系（需要反向映射：占位符->原始数字）
                    mapping = {v: k for k, v in desensitizer.number_mapping.items()}

                    results.append({
                        'filename': file.name,
                        'original_content': content,
                        'desensitized_content': desensitized_content,
                        'mapping': mapping,
                        'count': len(mapping)
                    })
                
                # 显示统计
                st.success("✅ 脱敏完成！")
                
                total_replacements = sum(r['count'] for r in results)
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("处理文件数", len(results))
                with col2:
                    st.metric("替换数字数", total_replacements)
                
                # 显示详细结果
                for result in results:
                    with st.expander(f"📄 {result['filename']} - 替换了 {result['count']} 个数字"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("原始内容（前500字符）")
                            st.text(result['original_content'][:500])
                        with col2:
                            st.subheader("脱敏后内容（前500字符）")
                            st.text(result['desensitized_content'][:500])
                        
                        # 显示映射关系
                        st.subheader("映射关系（前10条）")
                        mapping_preview = dict(list(result['mapping'].items())[:10])
                        st.json(mapping_preview)
                
                # 下载按钮
                st.subheader("下载脱敏结果")
                
                # 创建ZIP文件
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for result in results:
                        # 添加脱敏文件
                        desensitized_filename = f"{Path(result['filename']).stem}_desensitized{Path(result['filename']).suffix}"
                        zip_file.writestr(desensitized_filename, result['desensitized_content'])
                        
                        # 添加映射文件
                        mapping_filename = f"{Path(result['filename']).stem}_desensitized_map.json"
                        zip_file.writestr(mapping_filename, json.dumps(result['mapping'], ensure_ascii=False, indent=2))
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="📥 下载所有脱敏文件（ZIP）",
                    data=zip_buffer,
                    file_name="desensitized_files.zip",
                    mime="application/zip"
                )
                
            except Exception as e:
                st.error(f"❌ 脱敏失败: {str(e)}")

# Tab 2: 数据还原
with tab2:
    st.header("数据还原")
    
    st.info("上传脱敏文件和对应的映射文件，系统会还原原始数据")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("上传脱敏文件")
        desensitized_files = st.file_uploader(
            "选择脱敏后的文件",
            type=['md', 'txt', 'csv', 'json', 'xml', 'html', 'py', 'js'],
            accept_multiple_files=True,
            key="restore_files"
        )
    
    with col2:
        st.subheader("上传映射文件")
        mapping_file = st.file_uploader(
            "选择映射文件（JSON）",
            type=['json'],
            key="mapping_file"
        )
    
    # 还原按钮
    if st.button("🔓 开始还原", disabled=not (desensitized_files and mapping_file)):
        with st.spinner("正在还原..."):
            try:
                # 读取映射文件
                mapping = json.loads(mapping_file.read().decode('utf-8'))
                
                desensitizer = TextDesensitizer()
                results = []
                
                # 处理每个文件
                for file in desensitized_files:
                    # 读取文件内容
                    try:
                        content = file.read().decode('utf-8')
                    except UnicodeDecodeError:
                        content = file.read().decode('gbk')
                    
                    # 还原
                    restored_content = desensitizer.restore_content(content, mapping)
                    
                    results.append({
                        'filename': file.name,
                        'desensitized_content': content,
                        'restored_content': restored_content
                    })
                
                # 显示结果
                st.success("✅ 还原完成！")
                
                st.metric("还原文件数", len(results))
                
                # 显示详细结果
                for result in results:
                    with st.expander(f"📄 {result['filename']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("脱敏内容（前500字符）")
                            st.text(result['desensitized_content'][:500])
                        with col2:
                            st.subheader("还原内容（前500字符）")
                            st.text(result['restored_content'][:500])
                
                # 下载按钮
                st.subheader("下载还原结果")
                
                # 创建ZIP文件
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for result in results:
                        # 添加还原文件
                        restored_filename = f"{Path(result['filename']).stem}_restored{Path(result['filename']).suffix}"
                        zip_file.writestr(restored_filename, result['restored_content'])
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="📥 下载所有还原文件（ZIP）",
                    data=zip_buffer,
                    file_name="restored_files.zip",
                    mime="application/zip"
                )
                
            except Exception as e:
                st.error(f"❌ 还原失败: {str(e)}")

# Tab 3: 帮助
with tab3:
    st.header("帮助文档")
    
    st.markdown("""
    ## 📖 使用指南
    
    ### 1. 数据脱敏
    
    #### 功能说明：
    - 自动识别文本中的敏感数字
    - 使用占位符（如￥1￥、￥2￥）替换敏感数字
    - 保留章节编号、表格编号、图片编号等结构性数字
    - 生成映射文件用于后续还原
    
    #### 使用步骤：
    1. 在"数据脱敏"标签页上传文件
    2. 点击"开始脱敏"按钮
    3. 查看脱敏结果和统计信息
    4. 下载脱敏文件和映射文件（ZIP格式）
    
    #### 保留的数字类型：
    - ✅ 章节编号（如：1.1、2.3.1）
    - ✅ 表格编号（如：表1、表A.1）
    - ✅ 图片编号（如：图1、图A.1）
    - ✅ 附录编号（如：附录A、附录A.1）
    - ✅ 参考文献编号（如：[1]）
    
    #### 脱敏的数字类型：
    - ❌ 文本中的普通数字
    - ❌ 数据值
    - ❌ 统计数字
    - ❌ 测量值
    
    ### 2. 数据还原
    
    #### 功能说明：
    - 使用映射文件将脱敏数据还原为原始数据
    - 支持批量还原
    
    #### 使用步骤：
    1. 在"数据还原"标签页上传脱敏文件
    2. 上传对应的映射文件（JSON格式）
    3. 点击"开始还原"按钮
    4. 查看还原结果
    5. 下载还原文件（ZIP格式）
    
    ### 3. 支持的文件格式
    
    | 格式 | 扩展名 | 说明 |
    |------|--------|------|
    | Markdown | .md | Markdown文档 |
    | 文本 | .txt | 纯文本文件 |
    | CSV | .csv | 逗号分隔值文件 |
    | JSON | .json | JSON数据文件 |
    | XML | .xml | XML文档 |
    | HTML | .html, .htm | HTML网页 |
    | Python | .py | Python代码 |
    | JavaScript | .js | JavaScript代码 |
    
    ### 4. 脱敏示例
    
    **原始文本**:
    ```
    # 1.1 概述
    
    该矿井深度为500米，年产量达到100万吨。
    表1显示了详细数据。
    ```
    
    **脱敏后**:
    ```
    # 1.1 概述
    
    该矿井深度为￥1￥米，年产量达到￥2￥万吨。
    表1显示了详细数据。
    ```
    
    **映射文件**:
    ```json
    {
      "￥1￥": "500",
      "￥2￥": "100"
    }
    ```
    
    ### 5. 注意事项
    
    - ⚠️ 请妥善保管映射文件，丢失后无法还原
    - ⚠️ 脱敏文件和映射文件需要配对使用
    - ⚠️ 建议在脱敏前备份原始文件
    - ⚠️ 文件编码建议使用UTF-8
    
    ### 6. 常见问题
    
    **Q: 为什么有些数字没有被脱敏？**  
    A: 系统会自动保留章节编号、表格编号等结构性数字。
    
    **Q: 映射文件丢失了怎么办？**  
    A: 无法还原，请务必保管好映射文件。
    
    **Q: 可以对同一个文件多次脱敏吗？**  
    A: 不建议，会导致映射关系混乱。
    
    **Q: 支持哪些编码格式？**  
    A: 支持UTF-8和GBK编码。
    
    ---
    
    ## 🔗 相关链接
    
    - [GitHub仓库](#)
    - [技术文档](#)
    - [问题反馈](#)
    """)

# 页脚
st.divider()
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>数据脱敏工具 v1.0.0</p>
    <p>© 2024 数据安全工作组</p>
</div>
""", unsafe_allow_html=True)

