# LLM 智能检测系统 - Vue 3 前端

基于 Vue 3 + Vite 的现代化前端应用

## 🚀 快速开始

### 安装依赖
```bash
npm install
```

### 启动开发服务器
```bash
npm run dev
```

访问地址: http://localhost:5173

### 构建生产版本
```bash
npm run build
```

### 预览生产构建
```bash
npm run preview
```

## 📁 项目结构

```
frontend/
├── src/
│   ├── views/              # 页面组件
│   │   ├── Home.vue        # 首页
│   │   ├── Drawing/        # 制图检测模块
│   │   ├── Excel/          # Excel工单检测模块
│   │   └── Auth/           # 用户认证模块
│   ├── components/         # 公共组件
│   ├── stores/             # Pinia 状态管理
│   │   └── user.js         # 用户状态
│   ├── router/             # 路由配置
│   │   └── index.js
│   ├── utils/              # 工具函数
│   │   └── api.js          # API 请求封装
│   ├── App.vue             # 根组件
│   ├── main.js             # 入口文件
│   └── style.css           # 全局样式
├── public/                 # 静态资源
├── vite.config.js          # Vite 配置
└── package.json
```

## 🛠️ 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vite** - 下一代前端构建工具
- **Vue Router 4** - 官方路由管理器
- **Pinia** - Vue 3 状态管理
- **Axios** - HTTP 客户端

## 🔧 配置说明

### 开发代理配置

在 `vite.config.js` 中配置了开发代理，将以下请求转发到 Flask 后端 (http://localhost:5000):

- `/api/*` - API 接口
- `/auth/*` - 认证接口
- `/drawing/*` - 制图检测接口
- `/excel/*` - Excel 工单接口

### 环境要求

- Node.js 16+
- npm 或 yarn

## 📝 开发说明

### 添加新页面

1. 在 `src/views/` 创建页面组件
2. 在 `src/router/index.js` 添加路由配置
3. 在导航中添加链接

### API 调用

使用封装好的 axios 实例：

```javascript
import api from '@/utils/api'

// GET 请求
const data = await api.get('/api/v1/endpoint')

// POST 请求
const result = await api.post('/api/v1/endpoint', { data })
```

### 状态管理

使用 Pinia store：

```javascript
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
userStore.setUser(userData)
```

## 🎨 样式规范

- 使用 scoped CSS 避免样式污染
- 全局样式定义在 `src/style.css`
- 遵循 BEM 命名规范

## 📦 部署

### 构建生产版本

```bash
npm run build
```

构建产物在 `dist/` 目录，可以部署到任何静态服务器。

### 与 Flask 后端集成

1. 构建前端: `npm run build`
2. 将 `dist/` 目录内容复制到 Flask 的 `static/` 目录
3. 配置 Flask 路由返回 `index.html`

## 🔗 相关链接

- [Vue 3 文档](https://cn.vuejs.org/)
- [Vite 文档](https://cn.vitejs.dev/)
- [Vue Router 文档](https://router.vuejs.org/zh/)
- [Pinia 文档](https://pinia.vuejs.org/zh/)

## 📄 许可证

MIT License
