## How to Run

### Docker 方式（推荐）

```bash
docker-compose up --build -d
```

服务启动后访问：http://localhost:8081

生产部署时建议设置强随机 SECRET_KEY：
```bash
export SECRET_KEY=$(openssl rand -hex 32)
docker-compose up --build -d
```

### 本地开发方式

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

服务启动后访问：http://localhost:5000

### CLI 命令行方式

```bash
cd backend
pip install -r requirements.txt

# 基本用法
python convert.py input.bpmn                     # -> input.png
python convert.py input.bpmn -o output.png       # 指定输出路径
python convert.py input.bpmn -f svg -o flow.svg  # 输出 SVG
python convert.py input.bpmn --dpi 300 --scale 3 # 高清输出

# 测试示例
python convert.py samples/sample.bpmn -o samples/sample.png
```

### 系统依赖（Cairo 图形库）

本项目依赖 Cairo 进行 SVG → PNG 转换，需根据操作系统安装：

| 系统 | 安装命令 |
|------|---------|
| macOS | `brew install cairo pango` |
| Ubuntu/Debian | `apt-get install libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0` |
| Windows | 安装 [GTK3 Runtime](https://github.com/nickvdp/gtk3-runtime/releases)，或通过 MSYS2: `pacman -S mingw-w64-x86_64-cairo` |
| Docker | 无需手动安装，Dockerfile 已包含 |

### 测试与代码质量

```bash
cd backend

# 运行测试
python -m pytest tests/ -v

# 测试覆盖率
python -m pytest tests/ --cov=app --cov-report=term-missing

# Lint 检查
python -m ruff check app/ tests/

# Lint 自动修复
python -m ruff check app/ tests/ --fix

# 类型检查
python -m mypy app/
```

## Services

| 服务 | 端口 | 说明 |
|------|------|------|
| bpmn-converter | 8081 (Docker) / 5000 (本地) | BPMN 文件转图片服务（含 Web UI） |

访问地址：
- Docker 部署：http://localhost:8081
- 本地开发：http://localhost:5000

## 测试账号

本项目为工具类应用，无需登录，无测试账号。

## 题目内容

给我新写 Python 代码，实现将 BPMN 文件转化为图片的功能。

---

label-02948
