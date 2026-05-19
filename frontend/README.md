# Frontend

`frontend/` 是独立的 Vue 3 前端工程，负责聊天界面、会话管理、设置页、登录注册页和 API 请求封装。

## 技术栈

- Vue 3
- Vite
- TypeScript
- Pinia
- Vue Router
- Element Plus

## 目录说明

```text
frontend/
├─ src/
│  ├─ api/           # 前端 API 封装
│  ├─ composables/   # 组合式逻辑
│  ├─ mock/          # mock 数据与拦截器
│  ├─ router/        # 路由与守卫
│  ├─ stores/        # Pinia 状态
│  ├─ views/         # 页面级组件
│  ├─ styles/        # 全局样式
│  └─ utils/         # 请求与工具函数
├─ package.json
├─ vite.config.js
└─ .env.example
```

## 安装依赖

```bash
npm install
```

## 开发启动

```bash
npm run dev
```

默认地址：

- `http://127.0.0.1:5173`

## 构建生产包

```bash
npm run build
```

## 环境变量

复制示例配置：

```bash
cp .env.example .env
```

主要变量：

- `VITE_USE_MOCK`: 是否启用前端 mock
- `VITE_APP_ENV`: 当前前端环境标识
- `VITE_API_BASE_URL`: 显式指定后端基础地址
- `VITE_DEV_PROXY_TARGET`: Vite 开发代理目标地址

## 联调说明

- 当 `VITE_USE_MOCK=true` 时，前端优先使用本地 mock 数据
- 当 `VITE_USE_MOCK=false` 时，请确保后端服务已启动
- 开发环境下，`vite.config.js` 已配置 `/api/*` 代理到后端

## 推荐流程

前端独立开发：

```bash
npm run dev
```

前后端联调：

```bash
cd ..
python main.py
```
