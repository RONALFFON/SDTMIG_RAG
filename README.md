# SDTMIG_RAG - 智能知识库问答系统

基于 RAG (Retrieval-Augmented Generation) 技术的企业级智能知识库问答系统，采用前后端分离架构。

## 📋 项目简介

本项目演示了如何结合 **Milvus**（向量数据库）、**LangChain**（大模型应用框架）和 **DashScope**（通义千问大模型），构建一个私有知识库问答系统。

### 核心功能

- 📄 **文档上传与解析**：支持 PDF、Word、Excel、CSV、TXT 等多种格式
- 🔍 **智能检索**：基于向量相似度的语义检索
- 💬 **智能问答**：结合检索结果和大模型生成准确答案
- 🎨 **现代化界面**：ChatGPT 风格的对话界面

## 🏗️ 技术架构

### 后端 (Backend)

- **框架**：Flask + Flask-CORS
- **向量数据库**：Milvus 2.4.4
- **文档处理**：LangChain
- **Embedding 模型**：DashScope / HuggingFace
- **LLM**：DashScope (通义千问) / OpenAI 兼容接口

### 前端 (Frontend)

- **框架**：Vue 3 + TypeScript
- **构建工具**：Vite
- **状态管理**：Pinia
- **路由**：Vue Router
- **UI 组件**：Element Plus
- **样式**：Tailwind CSS

## 📁 项目结构

```
SDTMIG_RAG/
├── backend/              # 后端服务
│   ├── app/             # Flask 应用核心
│   │   ├── api_integration.py      # API 路由
│   │   ├── server.py               # Flask 应用工厂
│   │   ├── vector_db_manager.py    # 向量数据库管理
│   │   ├── vector_retriever.py     # 检索与问答
│   │   ├── document_loader.py      # 文档加载器
│   │   └── config.py               # 配置管理
│   ├── tests/           # 后端测试
│   ├── scripts/         # 辅助脚本
│   ├── manual_tests/    # 手动测试脚本
│   ├── data/            # 数据存储
│   │   └── uploads/     # 上传文件
│   ├── run.py           # 后端启动入口
│   ├── requirements.txt # Python 依赖
│   └── README.md        # 后端文档
│
├── frontend/            # 前端应用
│   ├── src/
│   │   ├── api/         # API 请求封装
│   │   ├── components/  # Vue 组件
│   │   ├── views/       # 页面视图
│   │   ├── stores/      # Pinia 状态管理
│   │   ├── router/      # 路由配置
│   │   ├── composables/ # 组合式函数
│   │   ├── utils/       # 工具函数
│   │   └── App.vue      # 根组件
│   ├── package.json     # Node.js 依赖
│   ├── vite.config.js   # Vite 配置
│   └── README.md        # 前端文档
│
├── docker/              # Docker 配置
│   ├── docker-compose.yml  # Milvus 服务编排
│   ├── embedEtcd.yaml      # etcd 配置
│   └── user.yaml           # Milvus 用户配置
│
├── docs/                # 项目文档
│   ├── PROJECT_DOCS.md                    # 详细项目文档
│   └── FRONTEND_AUTH_CHATGPT_PRD.md       # 前端需求文档
│
├── main.py              # 一键启动脚本
├── .gitignore          # Git 忽略配置
└── README.md           # 项目说明（本文件）
```

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- Docker & Docker Compose（用于运行 Milvus）

### 1. 启动 Milvus 向量数据库

```bash
cd docker
docker-compose up -d
```

等待 Milvus 服务启动（约 1-2 分钟），可通过以下命令检查：

```bash
docker-compose ps
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
# 后端配置
cp backend/.env.example backend/.env

# 前端配置（可选）
cp frontend/.env.example frontend/.env
```

编辑 `backend/.env`，配置必要的环境变量：

```env
# Milvus 配置
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
COLLECTION_NAME=agent_rag

# DashScope API Key（必填）
DASHSCOPE_API_KEY=your_api_key_here

# Embedding 模型
EMBEDDING_MODEL=dashscope

# LLM 配置
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
```

### 3. 安装依赖

#### 后端依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r backend/requirements.txt
```

#### 前端依赖

```bash
cd frontend
npm install
```

### 4. 启动服务

#### 方式一：一键启动（推荐）

```bash
python main.py
```

此命令会同时启动前后端：
- 后端：http://127.0.0.1:5000
- 前端：http://127.0.0.1:5173

#### 方式二：分别启动

**启动后端：**

```bash
python -m backend.run
```

**启动前端（新终端）：**

```bash
cd frontend
npm run dev
```

### 5. 访问应用

打开浏览器访问：http://127.0.0.1:5173

## 📖 使用说明

### 上传文档

1. 点击左侧"上传文档"按钮
2. 选择要上传的文件（支持 PDF、Word、Excel、CSV、TXT）
3. 等待文档处理完成（解析、切分、向量化）
4. 处理完成后即可进行问答

### 智能问答

1. 在对话框输入问题
2. 系统会自动检索相关文档片段
3. 结合检索结果生成答案
4. 可查看引用的源文档

## 🔧 开发指南

### 后端开发

```bash
# 运行测试
python -m unittest discover -s backend/tests -v

# 查看后端日志
tail -f backend/backend.log
```

### 前端开发

```bash
cd frontend

# 开发模式
npm run dev

# 构建生产版本
npm run build

# 预览生产版本
npm run preview

# 类型检查
npm run type-check
```

### Mock 模式

前端支持 Mock 模式，可在后端未就绪时独立开发：

编辑 `frontend/.env`：

```env
VITE_USE_MOCK=true
```

## 🐳 Docker 部署

### 构建生产镜像

```bash
# 构建后端镜像
docker build -t sdtmig-rag-backend ./backend

# 构建前端镜像
docker build -t sdtmig-rag-frontend ./frontend
```

### 使用 Docker Compose 部署

创建 `docker-compose.prod.yml`：

```yaml
version: '3.8'

services:
  backend:
    image: sdtmig-rag-backend
    ports:
      - "5000:5000"
    environment:
      - MILVUS_HOST=milvus
      - MILVUS_PORT=19530
    depends_on:
      - milvus

  frontend:
    image: sdtmig-rag-frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  milvus:
    image: milvusdb/milvus:v2.4.4
    # ... Milvus 配置
```

## 📚 相关文档

- [详细项目文档](docs/PROJECT_DOCS.md) - 包含核心概念、架构设计、代码详解
- [前端需求文档](docs/FRONTEND_AUTH_CHATGPT_PRD.md) - 前端功能需求说明
- [后端文档](backend/README.md) - 后端 API 和开发指南
- [前端文档](frontend/README.md) - 前端组件和开发指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 🔗 相关链接

- [Milvus 官方文档](https://milvus.io/docs)
- [LangChain 文档](https://python.langchain.com/)
- [Vue 3 文档](https://vuejs.org/)
- [DashScope 文档](https://help.aliyun.com/zh/dashscope/)

## 📞 联系方式

如有问题，请提交 Issue 或联系项目维护者。
