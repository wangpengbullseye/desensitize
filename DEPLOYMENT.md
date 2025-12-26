# 数据脱敏工具 - 部署指南

## 🚀 本地部署

### 1. 安装依赖

```bash
cd desensitize
pip install -r requirements.txt
```

### 2. 运行应用

```bash
streamlit run app.py
```

应用将在浏览器中自动打开：`http://localhost:8502`

---

## ☁️ 部署到Streamlit Cloud

### 准备工作

确保项目包含以下文件：
- ✅ `app.py` - 主应用文件
- ✅ `requirements.txt` - 依赖列表
- ✅ `advanced_desensitize_markdown.py` - 核心逻辑
- ✅ `.streamlit/config.toml` - 配置文件（可选）

### 部署步骤

#### 1. 上传到GitHub

```bash
cd desensitize

# 初始化Git仓库
git init

# 添加文件
git add app.py requirements.txt advanced_desensitize_markdown.py .streamlit/

# 提交
git commit -m "Initial commit: 数据脱敏工具"

# 推送到GitHub
git remote add origin https://github.com/your-username/desensitize-tool.git
git branch -M main
git push -u origin main
```

#### 2. 连接Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用GitHub账号登录
3. 点击 "New app"
4. 选择仓库：`desensitize-tool`
5. 选择分支：`main`
6. 主文件路径：`app.py`
7. 点击 "Deploy"

等待几分钟，应用就会部署完成！

---

## 🐳 Docker部署

### 1. 创建Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY app.py .
COPY advanced_desensitize_markdown.py .
COPY .streamlit/ .streamlit/

EXPOSE 8502

HEALTHCHECK CMD curl --fail http://localhost:8502/_stcore/health

CMD ["streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0"]
```

### 2. 构建镜像

```bash
docker build -t desensitize-app .
```

### 3. 运行容器

```bash
docker run -p 8502:8502 desensitize-app
```

访问：`http://localhost:8502`

### 4. 使用Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  desensitize-app:
    build: .
    ports:
      - "8502:8502"
    restart: unless-stopped
```

运行：
```bash
docker-compose up -d
```

---

## 📦 其他部署选项

### Heroku

1. 创建 `Procfile`:
```
web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0
```

2. 创建 `setup.sh`:
```bash
mkdir -p ~/.streamlit/

echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
\n\
" > ~/.streamlit/config.toml
```

3. 部署:
```bash
heroku create your-app-name
git push heroku main
```

### AWS EC2

1. 启动EC2实例（Ubuntu）
2. 安装依赖:
```bash
sudo apt update
sudo apt install python3-pip
pip3 install -r requirements.txt
```

3. 运行应用:
```bash
streamlit run app.py --server.port=8502 --server.address=0.0.0.0
```

4. 配置安全组，开放8502端口

### Azure App Service

使用Azure App Service部署Streamlit应用：

1. 创建App Service
2. 配置Python运行时
3. 部署代码
4. 设置启动命令：
```
streamlit run app.py --server.port=8000 --server.address=0.0.0.0
```

---

## ⚙️ 配置说明

### .streamlit/config.toml

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
headless = true
port = 8502
enableCORS = false
enableXsrfProtection = true
maxUploadSize = 200
```

### 环境变量

```bash
export STREAMLIT_SERVER_PORT=8502
export STREAMLIT_SERVER_ADDRESS=0.0.0.0
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=200
```

---

## 🔒 安全配置

### 1. 文件上传限制

在 `config.toml` 中设置：
```toml
[server]
maxUploadSize = 200  # MB
```

### 2. HTTPS配置

生产环境建议使用HTTPS：
- Streamlit Cloud自动提供HTTPS
- 自托管需要配置反向代理（Nginx）

### 3. 访问控制

使用Streamlit的密码保护功能：

创建 `.streamlit/secrets.toml`:
```toml
password = "your-secure-password"
```

在 `app.py` 中添加：
```python
import streamlit as st

def check_password():
    def password_entered():
        if st.session_state["password"] == st.secrets["password"]:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()
```

---

## 📊 性能优化

### 1. 缓存

使用Streamlit缓存：
```python
@st.cache_data
def load_file(file):
    return file.read().decode('utf-8')
```

### 2. 文件大小限制

```toml
[server]
maxUploadSize = 200
maxMessageSize = 200
```

### 3. 内存管理

定期清理临时文件：
```python
import tempfile
import shutil

# 使用临时目录
with tempfile.TemporaryDirectory() as tmpdir:
    # 处理文件
    pass
# 自动清理
```

---

## 🐛 故障排查

### 问题1: 模块导入错误

**解决**: 确保 `requirements.txt` 包含所有依赖
```bash
pip freeze > requirements.txt
```

### 问题2: 端口被占用

**解决**: 更改端口
```bash
streamlit run app.py --server.port=8503
```

### 问题3: 文件上传失败

**解决**: 检查文件大小限制和格式

### 问题4: 内存不足

**解决**: 
- 限制文件大小
- 使用流式处理
- 增加服务器内存

---

## 📞 技术支持

如有问题，请：
- 查看 [Streamlit文档](https://docs.streamlit.io)
- 提交GitHub Issue
- 联系技术支持团队

---

**版本**: 1.0.0  
**更新日期**: 2024-12-26

