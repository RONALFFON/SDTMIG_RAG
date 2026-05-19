# Backend

`backend/` 是独立的 Flask 后端服务，负责文档上传、向量入库、知识检索和问答接口。

## 技术栈

- Flask
- Flask-CORS
- LangChain
- Milvus
- DashScope / OpenAI 兼容接口

## 目录说明

```text
backend/
├─ app/
│  ├─ api_integration.py     # 向量检索相关接口
│  ├─ server.py              # Flask 应用工厂
│  ├─ vector_db_manager.py   # 向量库管理
│  ├─ vector_retriever.py    # 检索与问答
│  ├─ document_loader.py     # 文档加载
│  └─ config.py              # 环境变量与路径配置
├─ tests/                    # 自动化测试
├─ scripts/                  # 辅助脚本
├─ manual_tests/             # 手工验证脚本
├─ run.py                    # 后端启动入口
├─ requirements.txt
└─ .env.example
```

## 安装依赖

建议在虚拟环境中安装：

```bash
pip install -r backend/requirements.txt
```

## 启动方式

项目根目录执行：

```bash
python -m backend.run
```

默认地址：

- `http://127.0.0.1:5000`

## 环境变量

复制示例配置：

```bash
cp backend/.env.example backend/.env
```

主要变量：

- `FLASK_HOST`
- `FLASK_PORT`
- `FLASK_DEBUG`
- `MILVUS_HOST`
- `MILVUS_PORT`
- `COLLECTION_NAME`
- `DASHSCOPE_API_KEY`
- `EMBEDDING_MODEL`
- `LLM_BASE_URL`
- `LLM_MODEL`

后端会按以下顺序加载配置：

1. `backend/.env`
2. 项目根目录 `.env`

## 主要接口

当前核心接口统一挂在 `/api/vector` 下：

- `POST /api/vector/upload_document`
- `POST /api/vector/upload_file`
- `GET /api/vector/upload_task/<task_id>`
- `POST /api/vector/query`
- `POST /api/vector/search`
- `GET /api/vector/collection_info`
- `POST /api/vector/clear_collection`

## 测试

运行后端测试：

```bash
python -m unittest discover -s backend/tests -v
```

特点：

- 不依赖真实 Milvus
- 不依赖真实 LLM
- 适合快速回归接口层逻辑
