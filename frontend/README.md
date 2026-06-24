# Frontend - RAG 前端应用

基于 Vue 3 的现代化前端应用，提供 ChatGPT 风格的智能问答界面。

## 🛠️ 技术栈

- **框架**：Vue 3.5+ (Composition API)
- **构建工具**：Vite 7+
- **语言**：TypeScript 5+
- **状态管理**：Pinia 3
- **路由**：Vue Router 4
- **UI 组件**：Element Plus 2.11+
- **样式**：Tailwind CSS 3
- **HTTP 客户端**：Axios
- **图标**：Lucide Vue Next

## 📁 目录结构

```
frontend/
├── src/
│   ├── api/                    # API 请求封装
│   │   ├── auth.ts            # 认证相关接口
│   │   ├── chat.ts            # 聊天相关接口
│   │   └── user.ts            # 用户相关接口
│   │
│   ├── assets/                 # 静态资源
│   │   ├── base.css           # 基础样式
│   │   └── main.css           # 主样式
│   │
│   ├── components/             # 可复用组件
│   │   ├── RagChat.vue        # 聊天组件
│   │   ├── HelloWorld.vue     # 示例组件
│   │   ├── TheWelcome.vue     # 欢迎组件
│   │   ├── WelcomeItem.vue    # 欢迎项组件
│   │   └── icons/             # 图标组件
│   │
│   ├── composables/            # 组合式函数
│   │   └── useAutoRefreshToken.ts  # Token 自动刷新
│   │
│   ├── mock/                   # Mock 数据
│   │   ├── auth.mock.ts       # 认证 Mock
│   │   ├── chat.mock.ts       # 聊天 Mock
│   │   └── setup.ts           # Mock 配置
│   │
│   ├── router/                 # 路由配置
│   │   ├── index.ts           # 路由定义
│   │   └── guard.ts           # 路由守卫
│   │
│   ├── stores/                 # Pinia 状态管理
│   │   ├── auth.ts            # 认证状态
│   │   └── chat.ts            # 聊天状态
│   │
│   ├── styles/                 # 全局样式
│   │   └── global.css         # 全局样式文件
│   │
│   ├── utils/                  # 工具函数
│   │   ├── request.ts         # Axios 封装
│   │   ├── format.ts          # 格式化工具
│   │   └── validators.ts      # 验证器
│   │
│   ├── views/                  # 页面视图
│   │   ├── auth/              # 认证页面
│   │   │   └── LoginPage.vue  # 登录页
│   │   ├── chat/              # 聊天页面
│   │   └── settings/          # 设置页面
│   │
│   ├── App.vue                 # 根组件
│   ├── main.ts                 # 应用入口
│   └── env.d.ts                # 环境变量类型
│
├── public/                     # 公共静态资源
├── package.json                # 依赖配置
├── vite.config.js              # Vite 配置
├── tailwind.config.js          # Tailwind 配置
├── tsconfig.json               # TypeScript 配置
├── postcss.config.js           # PostCSS 配置
├── vite.log                    # 开发日志（自动生成）
└── README.md                   # 本文档
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

**Node.js 版本要求：** `^20.19.0 || >=22.12.0`

### 2. 配置环境变量

复制环境变量示例文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
# 是否启用 Mock 模式（true/false）
VITE_USE_MOCK=false

# 环境标识（development/production/sandbox）
VITE_APP_ENV=development

# 后端 API 基础地址（可选，开发环境使用代理）
VITE_API_BASE_URL=

# Vite 开发代理目标地址
VITE_DEV_PROXY_TARGET=http://127.0.0.1:5000
```

### 3. 启动开发服务器

```bash
npm run dev
```

**默认地址：** http://127.0.0.1:5173

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist/` 目录。

### 5. 预览生产版本

```bash
npm run preview
```

## 🎯 开发模式

### Mock 模式

前端支持 Mock 模式，可在后端未就绪时独立开发和测试：

**启用 Mock：**
```env
VITE_USE_MOCK=true
```

**Mock 功能：**
- ✅ 模拟用户认证
- ✅ 模拟聊天对话
- ✅ 模拟文档上传
- ✅ 无需后端服务

**Mock 数据位置：** `src/mock/`

### 联调模式

与后端服务联调：

**关闭 Mock：**
```env
VITE_USE_MOCK=false
```

**启动后端：**
```bash
# 在项目根目录
python main.py
```

**开发代理配置：**

`vite.config.js` 已配置 `/api/*` 代理到后端：

```javascript
server: {
  proxy: {
    '/api': {
      target: 'http://127.0.0.1:5000',
      changeOrigin: true
    }
  }
}
```

## 📡 API 集成

### 请求封装

所有 API 请求通过 `src/utils/request.ts` 统一封装：

- ✅ 自动添加 Token
- ✅ 统一错误处理
- ✅ 请求/响应拦截器
- ✅ Mock 模式支持

### API 模块

#### auth.ts - 认证接口

```typescript
// 登录
login(credentials: LoginCredentials): Promise<AuthResponse>

// 注册
register(userData: RegisterData): Promise<AuthResponse>

// 登出
logout(): Promise<void>

// 刷新 Token
refreshToken(): Promise<TokenResponse>
```

#### chat.ts - 聊天接口

```typescript
// 发送消息
sendMessage(message: ChatMessage): Promise<ChatResponse>

// 获取历史记录
getChatHistory(): Promise<ChatHistory[]>

// 上传文档
uploadDocument(file: File): Promise<UploadResponse>

// 查询任务状态
getUploadTaskStatus(taskId: string): Promise<TaskStatus>
```

#### user.ts - 用户接口

```typescript
// 获取用户信息
getUserInfo(): Promise<UserInfo>

// 更新用户信息
updateUserInfo(data: UpdateUserData): Promise<UserInfo>
```

## 🧩 核心组件

### RagChat.vue

主聊天组件，提供：
- 💬 消息输入与发送
- 📜 对话历史展示
- 📄 文档上传
- 🔄 实时响应流

### LoginPage.vue

登录页面，包含：
- 📱 手机号登录
- 🔐 密码输入
- ✅ 表单验证
- 🎨 现代化 UI

## 🗂️ 状态管理

### auth store

管理认证状态：
- `user`: 当前用户信息
- `token`: JWT Token
- `isLoggedIn`: 登录状态

**使用示例：**
```typescript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
await authStore.login(credentials)
```

### chat store

管理聊天状态：
- `messages`: 消息列表
- `currentConversation`: 当前对话
- `isLoading`: 加载状态

**使用示例：**
```typescript
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
await chatStore.sendMessage(message)
```

## 🛣️ 路由配置

### 路由结构

```typescript
/
├── /login          # 登录页
├── /chat           # 聊天页（需要认证）
├── /settings       # 设置页（需要认证）
└── /history        # 历史记录（需要认证）
```

### 路由守卫

`src/router/guard.ts` 实现：
- 🔒 未登录用户重定向到登录页
- ✅ 已登录用户访问登录页重定向到聊天页
- 🔄 Token 过期自动刷新

## 🎨 样式系统

### Tailwind CSS

项目使用 Tailwind CSS 进行样式开发：

```bash
# Tailwind 配置文件
tailwind.config.js
```

**使用示例：**
```vue
<template>
  <div class="flex items-center p-4 bg-white rounded-lg shadow">
    <h1 class="text-2xl font-bold text-gray-800">标题</h1>
  </div>
</template>
```

### Element Plus

UI 组件库，按需导入：

```vue
<template>
  <el-button type="primary">按钮</el-button>
  <el-input v-model="value" placeholder="请输入" />
</template>
```

## 🔧 开发指南

### 添加新页面

1. **创建页面组件：**
   ```vue
   <!-- src/views/NewPage.vue -->
   <template>
     <div class="new-page">
       <h1>新页面</h1>
     </div>
   </template>
   
   <script setup lang="ts">
   // 页面逻辑
   </script>
   ```

2. **添加路由：**
   ```typescript
   // src/router/index.ts
   {
     path: '/new-page',
     name: 'NewPage',
     component: () => import('@/views/NewPage.vue'),
     meta: { requiresAuth: true }
   }
   ```

### 添加新 API

1. **定义接口类型：**
   ```typescript
   // src/api/types.ts
   export interface NewApiResponse {
     data: string
   }
   ```

2. **实现 API 函数：**
   ```typescript
   // src/api/newApi.ts
   import request from '@/utils/request'
   
   export async function getNewData(): Promise<NewApiResponse> {
     return request.get('/api/new-endpoint')
   }
   ```

3. **添加 Mock（可选）：**
   ```typescript
   // src/mock/newApi.mock.ts
   import Mock from 'mockjs'
   
   Mock.mock('/api/new-endpoint', 'get', {
     data: 'mock data'
   })
   ```

### 添加组合式函数

```typescript
// src/composables/useNewFeature.ts
import { ref } from 'vue'

export function useNewFeature() {
  const data = ref(null)
  
  const fetchData = async () => {
    // 实现逻辑
  }
  
  return {
    data,
    fetchData
  }
}
```

## 📝 代码规范

### Vue 组件规范

- ✅ 使用 `<script setup lang="ts">`
- ✅ 使用 Composition API
- ✅ Props 使用 `defineProps`
- ✅ Emits 使用 `defineEmits`

### TypeScript 规范

- ✅ 优先使用 `interface` 定义类型
- ✅ 避免使用 `any`
- ✅ 导出类型使用 `export type`

### 命名规范

- **组件**：PascalCase（如 `RagChat.vue`）
- **文件**：kebab-case（如 `use-auto-refresh.ts`）
- **变量**：camelCase（如 `userName`）
- **常量**：UPPER_SNAKE_CASE（如 `API_BASE_URL`）

## 🐛 常见问题

### 依赖安装失败

**问题：** `npm install` 失败

**解决：**
```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

### 代理不生效

**问题：** API 请求 404

**解决：**
1. 检查 `vite.config.js` 中的代理配置
2. 确认后端服务已启动
3. 重启开发服务器

### TypeScript 类型错误

**问题：** 类型检查失败

**解决：**
```bash
# 运行类型检查
npm run type-check

# 查看具体错误
npm run type-check -- --noEmit
```

### Mock 数据不生效

**问题：** Mock 模式下仍然请求真实 API

**解决：**
1. 检查 `.env` 中 `VITE_USE_MOCK=true`
2. 确认 `src/mock/setup.ts` 已正确导入
3. 重启开发服务器

## 🚀 部署

### 构建生产版本

```bash
npm run build
```

### 部署到 Nginx

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /var/www/sdtmig-rag-frontend/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://backend-server:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Docker 部署

```dockerfile
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 📚 相关文档

- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Pinia 文档](https://pinia.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [Tailwind CSS 文档](https://tailwindcss.com/)

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- ✨ ChatGPT 风格聊天界面
- ✨ 用户认证系统
- ✨ 文档上传功能
- ✨ Mock 模式支持
- ✨ 响应式设计
