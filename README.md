# 汉化工作台

多 AI 协作翻译工具，支持 Claude / GPT-4o / Gemini 并行初译，逐段对话审稿，术语表管理。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python server.py

# 3. 浏览器访问
# http://localhost:8000
```

## 使用流程

### 翻译模式
1. 首页点「新建翻译」，上传 Paratranz 导出的原文 CSV
2. 三个 AI 并行初译全文（需在设置里配置 API Key）
3. 逐段在三列对话区查看译文，可追问修改
4. 点「使用此译」填入定稿区，编辑后点「确认」
5. 完成后点「导出 CSV」，格式：key, original, translation

### 校对模式
1. 首页点「新建校对」，上传原文 CSV + 机翻译文 CSV（可选）
2. 机翻内容自动填入定稿区，AI 同步生成校对建议
3. 逐段审阅修改

## 数据存储

所有数据存储在 `data/` 目录下的 JSON 文件：

```
data/
├── settings.json     API Keys 和提示词
├── glossary.json     术语表
└── projects/
    └── {id}.json     每个翻译项目
```

跨设备同步：将 `data/` 文件夹放入 Dropbox / iCloud 即可。

## CSV 格式

**输入（原文）**
```
key,original
0,First paragraph text
1,Second paragraph text
```

**输出（含译文）**
```
key,original,translation
0,First paragraph text,第一段译文
1,Second paragraph text,第二段译文
```

## 术语表

工作台中随时可添加术语：
- 每段原文自动高亮匹配术语
- 匹配到的术语自动注入 AI 对话的上下文
- 可通过标签分类管理

## API Keys 配置

在「设置」页面填写，保存后加密存储在本地 `data/settings.json`。

支持：
- Anthropic Claude（claude-opus-4-5）
- OpenAI GPT-4o
- Google Gemini 2.0 Flash

三个 Key 可以只配置其中几个，未配置的 AI 列会显示为不可用。
