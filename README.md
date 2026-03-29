# 汉化工作台

多 AI 协作翻译审稿工具，支持 Claude / GPT-4o / Gemini 并行初译，逐段对话审稿，全局术语表管理，以及 Obsidian 知识库导出（开发中）。

---

## 快速启动

```bash
# 首次使用
bash setup.sh        # Mac/Linux
setup.bat            # Windows

# 之后每次
bash start.sh        # Mac/Linux
start.bat            # Windows
```

启动后访问 `http://localhost:8000`，在「设置」页填入 API Keys 即可开始使用。

---

## 项目结构

```
translation-tool/
├── server.py          # FastAPI 后端
├── index.html         # 前端（单文件 SPA）
├── requirements.txt
├── setup.sh / setup.bat
├── start.sh / start.bat
├── .gitignore
└── data/              # 运行时生成，不纳入 Git
    ├── settings.json  # API Keys 和提示词
    ├── glossary.json  # 全局术语表
    └── projects/
        └── {id}.json  # 每个翻译项目的完整数据
```

---

## 架构说明

### 后端（server.py）

基于 **FastAPI**，职责有两个：

1. **AI API 代理**：转发对 Anthropic / OpenAI / Google 的请求，解决浏览器直接调用的 CORS 限制
2. **数据持久化**：读写 `data/` 目录下的 JSON 文件

所有数据存为本地 JSON，不使用数据库。跨设备同步可将 `data/` 文件夹放入 Dropbox / iCloud 等同步工具管理。

主要 API 路由：

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/api/settings` | 读写设置（含 API Keys） |
| GET/POST | `/api/glossary` | 读写完整术语表 |
| POST/DELETE | `/api/glossary/entry` | 增删单条术语 |
| GET/POST | `/api/projects` | 项目列表 / 新建项目 |
| GET/PUT/DELETE | `/api/projects/{id}` | 单项目读写删除 |
| PATCH | `/api/projects/{id}/segment/{idx}` | 更新单个段落（消息历史、定稿） |
| PATCH | `/api/projects/{id}/cursor` | 记录断点位置 |
| PATCH | `/api/projects/{id}/cache` | 写入 AI 初译缓存 |
| POST | `/api/ai/claude` | 转发 Claude 请求 |
| POST | `/api/ai/openai` | 转发 GPT-4o 请求 |
| POST | `/api/ai/gemini` | 转发 Gemini 请求 |

### 前端（index.html）

单文件 SPA，无构建工具，无框架依赖。页面结构：

| 页面 ID | 入口 | 说明 |
|---------|------|------|
| `page-home` | 顶栏「首页」 | 新建项目 + 最近项目列表 |
| `page-history` | 顶栏「历史」 | 所有项目表格，支持搜索和删除 |
| `page-glossary` | 顶栏「术语表」 | 术语管理，支持行内编辑、批量导入、导出 .md |
| `page-settings` | 顶栏「设置」 | API Keys + 翻译提示词 |
| `page-workspace` | 进入项目后 | 核心工作台 |

### 数据模型

每个项目（`data/projects/{id}.json`）的结构：

```json
{
  "id": "20260329143000-a1b2",
  "meta": {
    "filename": "On Slack.md.csv",
    "mode": "translate",
    "createdAt": "2026-03-29T14:30:00",
    "total": 64
  },
  "entries": [
    { "key": "0", "original": "...", "existing": "" }
  ],
  "segments": [
    {
      "key": "0",
      "claude":  { "messages": [...], "latest": "..." },
      "gpt":     { "messages": [...], "latest": "..." },
      "gemini":  { "messages": [...], "latest": "..." },
      "final":   "定稿译文",
      "_touched": false
    }
  ],
  "cursor": 12,
  "aiCache": {
    "claude": ["译文0", "译文1", ...],
    "gpt":    [...],
    "gemini": [...]
  }
}
```

---

## 核心工作流

### 翻译模式（CSV 无译文列）

1. 上传 `key, original` 两列 CSV
2. 立即进入工作台，三个 AI 在后台并行分批初译（每批 25 段）
3. 每批完成后实时注入对应段落，侧边栏状态点实时更新
4. 逐段审阅：查看三个 AI 的译文，点「使用此译」填入定稿区，或直接编辑
5. 可对任意 AI 追问（Enter 发送，Shift+Enter 换行），保持完整对话历史
6. 点「确认」保存定稿，自动跳下一段
7. 导出 CSV（`key, original, translation`），可选文件名后缀

### 校对模式（CSV 含译文列）

与翻译模式流程相同，区别是：
- 现有译文自动预填入定稿区
- AI 初译同步进行，供对比参考
- 逐段追问 AI 时，系统自动将原文 + 现有译文一起带入上下文

### 术语表

- 工作台中，每次切换段落自动扫描原文，匹配到的术语在原文中高亮显示，并列在顶部术语栏
- 向 AI 发起请求时，匹配到的术语自动注入 system prompt
- 可在工作台直接添加术语（选中文字后点「+ 添加术语」可预填英文）
- 术语表管理页支持：搜索、按标签筛选、双击行内编辑、批量导入、导出为 Obsidian .md

---

## CSV 格式

**输入（翻译）**
```
0,First paragraph text
1,Second paragraph text
```

**输入（校对）**
```
0,First paragraph text,第一段现有译文
1,Second paragraph text,第二段现有译文
```

**输出**
```
0,First paragraph text,第一段定稿译文
1,Second paragraph text,第二段定稿译文
```

格式与 Paratranz 导出的 `.md.csv` 兼容，导出后可直接上传回 Paratranz。

---

## 段落状态说明

侧边栏每条段落右侧的状态点含义：

| 颜色 | 含义 |
|------|------|
| ⚫ 灰 | 未处理，AI 尚未翻译 |
| 🟡 黄 | AI 已给出译文，等待审阅 |
| 🟠 橙 | 定稿区有内容但未点「确认」 |
| 🟢 绿 | 已确认定稿 |

---

## 模型版本

| AI | 模型 | 说明 |
|----|------|------|
| Claude | `claude-opus-4-5` | 用于初译和逐段对话 |
| GPT-4o | `gpt-4o` | 用于初译和逐段对话 |
| Gemini | `gemini-2.5-flash` | 用于初译和逐段对话 |

如需修改模型，在 `server.py` 对应的代理函数中修改 `model` 字段（Claude/GPT），Gemini 的模型名在 URL 路径中修改。

---

## 注意事项

**API Keys 安全**
当前 Keys 以明文存储在 `data/settings.json`，服务仅监听 `127.0.0.1` 本地回环地址，局域网其他设备无法访问。后续计划改为系统钥匙串（keyring）存储。**不要将 `data/` 目录提交到 Git**（已在 `.gitignore` 中排除）。

**分批翻译**
初译按每批 25 段发送，避免超出模型输出 token 限制（主要针对 Gemini）。三个 AI 并行，每个 AI 内部串行处理各批次。如遇网络超时，已完成的批次结果已写入磁盘，重新打开项目不会丢失。

**断点续译**
项目数据实时写入 `data/projects/{id}.json`，关闭浏览器后重新打开、从历史记录进入项目，可从上次的断点继续。

**长文章**
目前每批 25 段、每次请求 max_tokens 设为 8000。特别长的文章（200+ 段）需要较多批次，初译时间较长，但不影响正常使用工作台。

**Paratranz 下划线标记**
Paratranz 界面中的下划线格式标记不是 Markdown 语法，导出 CSV 后不会出现，无需特殊处理。

---

## 待实现功能

- [ ] Obsidian 导出：对照存档模式（一文件）
- [ ] Obsidian 导出：提炼知识点模式（调 Claude API 拆分，多文件）
- [ ] API Keys 改用系统钥匙串（keyring）存储
- [ ] Paratranz API 直接拉取 / 推送（目前需手动下载上传 CSV）
- [ ] QQ 群进度播报自动化