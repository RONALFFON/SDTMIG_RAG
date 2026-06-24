# Backend - RAG 后端服务

独立的 Flask 后端服务，负责文档上传、向量入库、知识检索和问答接口。

## 🛠️ 技术栈

- **Web 框架**：Flask + Flask-CORS
- **向量数据库**：Milvus 2.4.4
- **文档处理**：LangChain
- **Embedding 模型**：DashScope / HuggingFace
- **LLM**：DashScope (通义千问) / OpenAI 兼容接口

## 📁 目录结构

```
backend/
├── app/                          # 核心应用代码
│   ├── __init__.py              # 包初始化
│   ├── api_integration.py       # API 路由与接口定义
│   ├── server.py                # Flask 应用工厂
│   ├── vector_db_manager.py     # 向量数据库管理器
│   ├── vector_retriever.py      # 检索与问答逻辑
│   ├── document_loader.py       # 文档加载与解析
│   └── config.py                # 配置管理
│
├── tests/                        # 自动化测试
│   └── test_query_api.py        # API 集成测试
│
├── scripts/                      # 辅助脚本
│   ├── query_system.py          # 查询系统脚本
│   ├── test_llm.py              # LLM 测试
│   └── upload_document.py       # 文档上传脚本
│
├── manual_tests/                 # 手动测试脚本
│   ├── milvus_create.py         # Milvus 创建测试
│   ├── milvus_inspect.py        # Milvus 检查脚本
│   └── milvus_search.py         # Milvus 搜索测试
│
├── data/                         # 数据存储
│   └── uploads/                 # 上传文件目录
│
├── run.py                        # 后端启动入口
├── requirements.txt              # Python 依赖
├── backend.log                   # 运行日志（自动生成）
└── README.md                     # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

建议在虚拟环境中安装：

```bash
# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
pip install -r backend/requirements.txt
```

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`，配置必要的环境变量：

```env
# Flask 配置
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=True

# Milvus 配置
MILVUS_HOST=127.0.0.1
MILVUS_PORT=19530
COLLECTION_NAME=agent_rag

# DashScope API Key（必填）
DASHSCOPE_API_KEY=your_api_key_here

# Embedding 模型配置
EMBEDDING_MODEL=dashscope
# 可选值：dashscope, huggingface, fake

# LLM 配置
LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-plus
# 可选模型：qwen-plus, qwen-max, qwen-turbo
```

**配置加载顺序：**
1. `backend/.env`（优先）
2. 项目根目录 `.env`（备选）

### 3. 启动服务

从项目根目录执行：

```bash
python -m backend.run
```

或使用一键启动脚本：

```bash
python main.py
```

**默认地址：** http://127.0.0.1:5000

## 📡 API 接口

所有接口统一挂在 `/api/vector` 路径下。

### 文档上传

#### POST /api/vector/upload_file

上传单个文件到知识库。

**请求参数：**
- `file`: 文件（multipart/form-data）
- `collection_name`: 集合名称（可选，默认使用环境变量配置）

**响应示例：**
```json
{
  "success": true,
  "message": "文件上传成功",
  "task_id": "abc123",
  "file_name": "document.pdf"
}
```

#### GET /api/vector/upload_task/<task_id>

查询上传任务状态。

**响应示例：**
```json
{
  "task_id": "abc123",
  "status": "processing",
  "progress": 65,
  "stage": "chunking",
  "detail": {
    "chunk_count": 150
  }
}
```

**任务状态：**
- `queued`: 排队中
- `processing`: 处理中
- `completed`: 完成
- `failed`: 失败

### 知识检索

#### POST /api/vector/query

智能问答接口。

**请求参数：**
```json
{
  "question": "什么是 RAG？",
  "collection_name": "agent_rag",
  "k": 5
}
```

**响应示例：**
```json
{
  "success": true,
  "answer": "RAG (Retrieval-Augmented Generation) 是一种...",
  "confidence": 0.85,
  "question_type": "概念解释",
  "sources": [
    {
      "content": "相关文档片段...",
      "score": 0.92,
      "metadata": {
        "source": "document.pdf",
        "page": 3
      }
    }
  ]
}
```

#### POST /api/vector/search

纯检索接口（不生成答案）。

**请求参数：**
```json
{
  "query": "向量数据库",
  "collection_name": "agent_rag",
  "k": 5
}
```

**响应示例：**
```json
{
  "success": true,
  "results": [
    {
      "content": "相关文档片段...",
      "score": 0.88,
      "metadata": {...}
    }
  ]
}
```

### 集合管理

#### GET /api/vector/collection_info

获取集合信息。

**响应示例：**
```json
{
  "success": true,
  "collection_name": "agent_rag",
  "document_count": 150,
  "is_initialized": true,
  "storage_mode": "milvus"
}
```

#### POST /api/vector/clear_collection

清空集合数据。

**请求参数：**
```json
{
  "collection_name": "agent_rag"
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "集合已清空"
}
```

## 🧪 测试

### 运行自动化测试

```bash
# 从项目根目录执行
python -m unittest discover -s backend/tests -v
```

**测试特点：**
- ✅ 不依赖真实 Milvus
- ✅ 不依赖真实 LLM
- ✅ 使用 Mock 对象模拟
- ✅ 适合快速回归测试

### 手动测试

使用 `manual_tests/` 目录下的脚本：

```bash
# 测试 Milvus 连接
python backend/manual_tests/milvus_create.py

# 测试搜索功能
python backend/manual_tests/milvus_search.py
```

### 使用辅助脚本

```bash
# 上传文档
python backend/scripts/upload_document.py --file path/to/doc.pdf

# 测试查询
python backend/scripts/query_system.py --question "什么是 RAG？"

# 测试 LLM
python backend/scripts/test_llm.py
```

## 📊 核心模块说明

### vector_db_manager.py

向量数据库管理器，负责：
- 文档切分（使用 RecursiveCharacterTextSplitter）
- 向量化（使用 DashScope/HuggingFace Embeddings）
- 存储到 Milvus
- 集合管理

### vector_retriever.py

检索与问答逻辑，负责：
- 向量相似度检索
- 问题分类
- 答案生成（结合 LLM）
- 结果排序

### document_loader.py

文档加载器，支持：
- PDF（PyPDFLoader）
- Word（Docx2txtLoader）
- Excel（UnstructuredExcelLoader）
- CSV（CSVLoader）
- TXT（TextLoader）

### api_integration.py

API 路由定义，包括：
- 文件上传与处理
- 异步任务管理
- 进度回调
- 错误处理

## 🔧 开发指南

### 添加新的 API 接口

在 `app/api_integration.py` 中添加路由：

```python
@vector_bp.route('/new_endpoint', methods=['POST'])
def new_endpoint():
    # 实现逻辑
    return jsonify({"success": True})
```

### 添加新的文档类型

在 `app/document_loader.py` 中扩展 `SUPPORTED_EXTENSIONS`：

```python
SUPPORTED_EXTENSIONS = {
    '.txt': 'text',
    '.csv': 'csv',
    '.pdf': 'pdf',
    '.docx': 'docx',
    '.md': 'markdown',  # 新增
}
```

### 调试技巧

1. **查看日志：**
   ```bash
   tail -f backend/backend.log
   ```

2. **启用详细日志：**
   在 `config.py` 中设置：
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

3. **测试单个模块：**
   ```python
   from backend.app.vector_db_manager import VectorDatabaseManager
   manager = VectorDatabaseManager()
   # 测试具体方法
   ```

## 🐛 常见问题

### Milvus 连接失败

**问题：** `ConnectionNotExistException: should create connection first`

**解决：**
1. 检查 Milvus 服务是否启动：`docker-compose ps`
2. 检查 `.env` 中的 `MILVUS_HOST` 和 `MILVUS_PORT`
3. 重启后端服务

### Embedding 模型加载失败

**问题：** `DashScope API Key 无效`

**解决：**
1. 检查 `DASHSCOPE_API_KEY` 是否正确
2. 访问 https://dashscope.console.aliyun.com/ 获取 API Key

### 文件上传失败

**问题：** `上传目录不存在`

**解决：**
```bash
mkdir -p backend/data/uploads
```

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ 支持文档上传与解析
- ✨ 实现向量检索与问答
- ✨ 集成 Milvus 向量数据库
- ✨ 支持多种文档格式
