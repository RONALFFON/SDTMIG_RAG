# SDTMIG_RAG

SDTMIG_RAG 已重构为前后端分离结构：

- `backend/`: Flask + Milvus + DashScope 的后端服务
- `frontend/`: Vue 3 + Vite + Pinia 的前端应用
- `main.py`: 根目录一键启动脚本，同时拉起前后端开发环境

## 目录结构

```text
SDTMIG_RAG/
├─ backend/
│  ├─ app/              # Flask 应用、接口、向量检索核心模块
│  ├─ tests/            # 后端自动化测试
│  ├─ scripts/          # 后端辅助脚本
│  ├─ manual_tests/     # 手工验证脚本
│  ├─ requirements.txt
│  └─ README.md
├─ frontend/
│  ├─ src/              # Vue 页面、组件、状态管理、API 封装
│  ├─ package.json
│  └─ README.md
├─ main.py              # 一键启动前后端
└─ README.md
```

## 快速开始

### 方式一：根目录一键启动

```bash
python main.py
```

默认行为：

- 后端启动在 `http://127.0.0.1:5000`
- 前端启动在 `http://127.0.0.1:5173`
- 前端开发模式下会通过 Vite 代理转发 `/api/*` 到后端

### 方式二：分别启动

后端：

```bash
python -m backend.run
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## 环境变量

- 后端示例配置见 `backend/.env.example`
- 前端示例配置见 `frontend/.env.example`
- 如需兼容旧习惯，也支持将 `.env` 放在项目根目录

## 测试

后端 API 集成测试位置：

- `backend/tests/test_query_api.py`

运行命令：

```bash
python -m unittest discover -s backend/tests -v
```

说明：

- 使用 Flask `test_client` 和 stub，不依赖真实 Milvus 与真实 LLM
- 当前主要覆盖 `/api/vector/query` 与 `/api/vector/upload_file`

## 当前说明

- 后端已独立为 `backend` 包，可单独部署和启动
- 前端已独立为 `frontend` 工程，可单独开发和构建
- 前端默认支持 `mock` 沙箱模式，便于在后端未全部实现时独立联调
