# 開發者快速入門

本文件協助開發者快速設定本機開發環境並開始開發。

---

## 目錄

1. [環境需求](#環境需求)
2. [專案結構](#專案結構)
3. [快速開始](#快速開始)
4. [後端開發](#後端開發)
5. [前端開發](#前端開發)
6. [桌面應用開發](#桌面應用開發)
7. [測試](#測試)
8. [程式碼規範](#程式碼規範)
9. [常用指令](#常用指令)

---

## 環境需求

### 必要工具

| 工具 | 版本 | 用途 |
|-----|------|------|
| Python | 3.11+ | 後端開發 |
| Node.js | 18+ | 前端開發 |
| Git | 2.30+ | 版本控制 |
| MySQL | 8.0+ 或 TiDB | 資料庫 |

### 建議工具

| 工具 | 用途 |
|-----|------|
| VS Code | 編輯器 |
| Docker | 容器化開發 |
| Postman | API 測試 |

---

## 專案結構

```
driver_management_system/
├── backend/                 # 雲端後端 (FastAPI)
│   ├── src/
│   │   ├── api/            # API 路由
│   │   ├── config/         # 設定
│   │   ├── middleware/     # 中間件
│   │   ├── models/         # 資料模型
│   │   ├── schemas/        # Pydantic Schema
│   │   ├── services/       # 商業邏輯
│   │   ├── utils/          # 工具函式
│   │   └── main.py         # 應用入口
│   ├── tests/              # 測試
│   └── requirements.txt    # Python 依賴
│
├── frontend/               # 前端 (Vue 3)
│   ├── src/
│   │   ├── api/           # API 呼叫
│   │   ├── components/    # 元件
│   │   ├── router/        # 路由
│   │   ├── stores/        # Pinia Store
│   │   ├── utils/         # 工具函式
│   │   ├── views/         # 頁面
│   │   └── App.vue        # 根元件
│   └── package.json       # Node 依賴
│
├── desktop_app/           # 本機桌面應用 (FastAPI)
│   ├── src/
│   │   ├── api/          # API 路由
│   │   ├── services/     # 服務
│   │   └── utils/        # 工具
│   └── requirements.txt
│
├── docs/                  # 文件
├── scripts/               # 腳本
└── specs/                 # 規格文件
```

---

## 快速開始

### 1. Clone 專案

```bash
git clone https://github.com/username/driver_management_system.git
cd driver_management_system
```

### 2. 設定環境變數

複製環境變數範本：

```bash
cp .env.example .env
```

編輯 `.env` 檔案，填入必要設定：

```bash
# 資料庫
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/driver_management

# JWT
JWT_SECRET_KEY=dev-secret-key-change-in-production

# 其他設定...
```

### 3. 啟動後端

```bash
cd backend

# 建立虛擬環境
python -m venv venv

# 啟用虛擬環境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安裝依賴
pip install -r requirements.txt

# 初始化資料庫
python ../scripts/init_database.py

# 啟動開發伺服器
uvicorn src.main:app --reload --port 8000
```

後端 API 將在 http://localhost:8000 運行。

API 文件：http://localhost:8000/docs

### 4. 啟動前端

開啟新的終端機：

```bash
cd frontend

# 安裝依賴
npm install

# 啟動開發伺服器
npm run dev
```

前端將在 http://localhost:5173 運行。

### 5. 登入系統

預設管理員帳號：
- 帳號：`admin`
- 密碼：`admin123`

---

## 後端開發

### 目錄說明

| 目錄 | 說明 |
|-----|------|
| `api/` | API 路由定義 |
| `models/` | SQLAlchemy ORM 模型 |
| `schemas/` | Pydantic 請求/回應模型 |
| `services/` | 商業邏輯服務 |
| `middleware/` | 中間件（認證、錯誤處理）|
| `utils/` | 工具函式 |

### 新增 API 端點

1. 在 `api/` 新增路由檔案：

```python
# api/example.py
from fastapi import APIRouter, Depends
from ..middleware.auth import get_current_user

router = APIRouter(prefix="/api/example", tags=["Example"])

@router.get("/")
async def list_examples(current_user = Depends(get_current_user)):
    return {"examples": []}
```

2. 在 `main.py` 註冊路由：

```python
from .api import example
app.include_router(example.router)
```

### 新增資料模型

1. 在 `models/` 新增模型：

```python
# models/example.py
from sqlalchemy import Column, Integer, String
from .base import Base

class Example(Base):
    __tablename__ = "examples"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
```

2. 在 `models/__init__.py` 匯出：

```python
from .example import Example
```

3. 執行資料庫遷移（或重新初始化）

### 新增服務

```python
# services/example_service.py
from sqlalchemy.orm import Session
from ..models.example import Example

class ExampleService:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self):
        return self.db.query(Example).all()

    def create(self, name: str):
        example = Example(name=name)
        self.db.add(example)
        self.db.commit()
        return example
```

---

## 前端開發

### 目錄說明

| 目錄 | 說明 |
|-----|------|
| `views/` | 頁面元件 |
| `components/` | 可重用元件 |
| `stores/` | Pinia 狀態管理 |
| `router/` | Vue Router 設定 |
| `api/` | API 呼叫函式 |
| `utils/` | 工具函式 |

### 新增頁面

1. 在 `views/` 新增頁面：

```vue
<!-- views/Example.vue -->
<template>
  <div class="example-page">
    <h1>Example Page</h1>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useExampleStore } from '@/stores/example'

const store = useExampleStore()

onMounted(() => {
  store.fetchExamples()
})
</script>
```

2. 在 `router/index.js` 新增路由：

```javascript
{
  path: '/example',
  name: 'Example',
  component: () => import('@/views/Example.vue'),
  meta: { requiresAuth: true }
}
```

### 新增 Store

```javascript
// stores/example.js
import { defineStore } from 'pinia'
import api from '@/utils/api'

export const useExampleStore = defineStore('example', {
  state: () => ({
    examples: [],
    loading: false
  }),

  actions: {
    async fetchExamples() {
      this.loading = true
      try {
        const response = await api.get('/api/example')
        this.examples = response.data
      } finally {
        this.loading = false
      }
    }
  }
})
```

### 新增元件

```vue
<!-- components/example/ExampleCard.vue -->
<template>
  <el-card class="example-card">
    <template #header>
      <span>{{ title }}</span>
    </template>
    <slot></slot>
  </el-card>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  }
})
</script>
```

---

## 桌面應用開發

### 啟動桌面應用

```bash
cd desktop_app

# 建立虛擬環境
python -m venv venv
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 啟動
uvicorn src.main:app --port 8001
```

### 主要功能

- PDF 處理與 OCR
- Google Drive 上傳
- OAuth Token 管理

---

## 測試

### 後端測試

```bash
cd backend

# 執行所有測試
pytest

# 執行特定測試
pytest tests/unit/test_example.py

# 顯示覆蓋率
pytest --cov=src --cov-report=html
```

### 前端測試

```bash
cd frontend

# 執行單元測試
npm run test:unit

# 執行 E2E 測試
npm run test:e2e
```

### 測試資料庫

建議使用獨立的測試資料庫：

```bash
# .env.test
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/driver_management_test
```

---

## 程式碼規範

### Python (後端)

使用 Black 和 Flake8：

```bash
# 格式化
black src/

# 檢查
flake8 src/
```

設定檔：`pyproject.toml`

### JavaScript/Vue (前端)

使用 ESLint 和 Prettier：

```bash
# 檢查
npm run lint

# 修復
npm run lint:fix

# 格式化
npm run format
```

設定檔：`.eslintrc.js`, `.prettierrc`

### Git Commit 規範

使用 Conventional Commits：

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

類型：
- `feat`: 新功能
- `fix`: 修復 Bug
- `docs`: 文件更新
- `style`: 程式碼格式
- `refactor`: 重構
- `test`: 測試
- `chore`: 雜項

範例：
```
feat(profiles): 新增履歷類型轉換功能

- 支援 basic 轉換為 event_investigation
- 支援 basic 轉換為 personnel_interview
- 新增轉換規則驗證

Closes #123
```

---

## 常用指令

### 後端

```bash
# 啟動開發伺服器
uvicorn src.main:app --reload --port 8000

# 初始化資料庫
python scripts/init_database.py

# 執行測試
pytest

# 格式化程式碼
black src/

# 檢查程式碼
flake8 src/
```

### 前端

```bash
# 啟動開發伺服器
npm run dev

# 建置生產版本
npm run build

# 預覽生產版本
npm run preview

# 執行測試
npm run test

# 檢查程式碼
npm run lint

# 格式化程式碼
npm run format
```

### Git

```bash
# 建立功能分支
git checkout -b feature/new-feature

# 提交變更
git add .
git commit -m "feat(scope): description"

# 推送分支
git push -u origin feature/new-feature

# 合併到主分支
git checkout main
git merge feature/new-feature
git push
```

---

## 除錯技巧

### 後端除錯

1. 使用 VS Code 的 Python 除錯器
2. 設定 `launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["src.main:app", "--reload"],
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### 前端除錯

1. 使用 Vue DevTools 瀏覽器擴充功能
2. 使用 `console.log()` 或 Vue 的 `debugger`

### API 測試

1. 使用 Swagger UI：http://localhost:8000/docs
2. 使用 Postman 匯入 OpenAPI spec

---

## 相關資源

- [FastAPI 文件](https://fastapi.tiangolo.com/)
- [Vue 3 文件](https://vuejs.org/)
- [Pinia 文件](https://pinia.vuejs.org/)
- [Element Plus 文件](https://element-plus.org/)
- [SQLAlchemy 文件](https://www.sqlalchemy.org/)

---

## 取得協助

- 查閱 `docs/` 目錄下的文件
- 提交 Issue 至 GitHub Repository
- 聯繫專案維護者
