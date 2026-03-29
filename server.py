"""
汉化工作台 - 后端服务
运行: python server.py
访问: http://localhost:8000
"""

import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# ── 数据目录 ──────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"
SETTINGS_FILE = DATA_DIR / "settings.json"
GLOSSARY_FILE = DATA_DIR / "glossary.json"

for d in [DATA_DIR, PROJECTS_DIR]:
    d.mkdir(exist_ok=True)


def read_json(path: Path, default=None):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default if default is not None else {}


def write_json(path: Path, data: Any):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ── 静态文件 ──────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse(BASE_DIR / "index.html")


# ── 设置 ──────────────────────────────────────────────
@app.get("/api/settings")
def get_settings():
    return read_json(SETTINGS_FILE, {
        "claudeKey": "", "openaiKey": "", "geminiKey": "",
        "systemPrompt": DEFAULT_SYSTEM_PROMPT,
        "proofreadPrompt": DEFAULT_PROOFREAD_PROMPT,
    })


@app.post("/api/settings")
async def save_settings(request: Request):
    data = await request.json()
    write_json(SETTINGS_FILE, data)
    return {"ok": True}


# ── 术语表 ────────────────────────────────────────────
@app.get("/api/glossary")
def get_glossary():
    return read_json(GLOSSARY_FILE, [])


@app.post("/api/glossary")
async def save_glossary(request: Request):
    data = await request.json()
    write_json(GLOSSARY_FILE, data)
    return {"ok": True}


@app.post("/api/glossary/entry")
async def add_glossary_entry(request: Request):
    entry = await request.json()
    entry["id"] = str(uuid.uuid4())[:8]
    entry.setdefault("tags", ["default"])
    entry.setdefault("note", "")
    glossary = read_json(GLOSSARY_FILE, [])
    glossary.append(entry)
    write_json(GLOSSARY_FILE, glossary)
    return entry


@app.put("/api/glossary/entry/{entry_id}")
async def update_glossary_entry(entry_id: str, request: Request):
    """更新单条术语"""
    patch = await request.json()
    glossary = read_json(GLOSSARY_FILE, [])
    for e in glossary:
        if e.get("id") == entry_id:
            for key in ("en", "zh", "note", "tags"):
                if key in patch:
                    e[key] = patch[key]
            write_json(GLOSSARY_FILE, glossary)
            return e
    raise HTTPException(404, "Entry not found")


@app.delete("/api/glossary/entry/{entry_id}")
def delete_glossary_entry(entry_id: str):
    glossary = read_json(GLOSSARY_FILE, [])
    glossary = [e for e in glossary if e.get("id") != entry_id]
    write_json(GLOSSARY_FILE, glossary)
    return {"ok": True}


# ── 项目 ──────────────────────────────────────────────
@app.get("/api/projects")
def list_projects():
    projects = []
    for f in sorted(PROJECTS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            p = json.loads(f.read_text(encoding="utf-8"))
            projects.append({
                "id": p["id"],
                "filename": p["meta"]["filename"],
                "mode": p["meta"]["mode"],
                "createdAt": p["meta"]["createdAt"],
                "total": p["meta"]["total"],
                "done": sum(1 for s in p.get("segments", []) if s.get("final")),
                "tags": p["meta"].get("tags", []),
            })
        except Exception:
            pass
    return projects


@app.post("/api/projects")
async def create_project(request: Request):
    data = await request.json()
    pid = datetime.now().strftime("%Y%m%d%H%M%S") + "-" + str(uuid.uuid4())[:4]
    project = {
        "id": pid,
        "meta": {
            "filename": data["filename"],
            "mode": data["mode"],  # "translate" | "proofread"
            "createdAt": datetime.now().isoformat(),
            "total": len(data["entries"]),
            "tags": data.get("tags", []),  # 项目标签
        },
        "entries": data["entries"],
        "segments": [
            {
                "key": e["key"],
                "claude":  {"messages": [], "latest": ""},
                "gpt":     {"messages": [], "latest": ""},
                "gemini":  {"messages": [], "latest": ""},
                "final":   e.get("existing", ""),
            }
            for e in data["entries"]
        ],
        "cursor": 0,
        "aiCache": {},
    }
    write_json(PROJECTS_DIR / f"{pid}.json", project)
    return {"id": pid}


@app.get("/api/projects/{pid}")
def get_project(pid: str):
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404, "Project not found")
    return read_json(f)


@app.put("/api/projects/{pid}")
async def update_project(pid: str, request: Request):
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404, "Project not found")
    data = await request.json()
    write_json(f, data)
    return {"ok": True}


@app.patch("/api/projects/{pid}/meta")
async def update_project_meta(pid: str, request: Request):
    """更新项目元数据（如标签）"""
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404)
    project = read_json(f)
    patch = await request.json()
    for key in ("tags",):
        if key in patch:
            project["meta"][key] = patch[key]
    write_json(f, project)
    return {"ok": True}


@app.patch("/api/projects/{pid}/segment/{idx}")
async def update_segment(pid: str, idx: int, request: Request):
    """部分更新某段落（避免每次保存整个项目）"""
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404)
    project = read_json(f)
    patch = await request.json()
    seg = project["segments"][idx]
    for key in ("final", "claude", "gpt", "gemini"):
        if key in patch:
            seg[key] = patch[key]
    project["segments"][idx] = seg
    write_json(f, project)
    return {"ok": True}


@app.patch("/api/projects/{pid}/cursor")
async def update_cursor(pid: str, request: Request):
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404)
    project = read_json(f)
    data = await request.json()
    project["cursor"] = data["cursor"]
    write_json(f, project)
    return {"ok": True}


@app.patch("/api/projects/{pid}/cache")
async def update_cache(pid: str, request: Request):
    f = PROJECTS_DIR / f"{pid}.json"
    if not f.exists():
        raise HTTPException(404)
    project = read_json(f)
    data = await request.json()
    project["aiCache"].update(data)
    write_json(f, project)
    return {"ok": True}


@app.delete("/api/projects/{pid}")
def delete_project(pid: str):
    f = PROJECTS_DIR / f"{pid}.json"
    if f.exists():
        f.unlink()
    return {"ok": True}


# ── AI 代理 ───────────────────────────────────────────
@app.post("/api/ai/claude")
async def proxy_claude(request: Request):
    settings = read_json(SETTINGS_FILE, {})
    api_key = settings.get("claudeKey", "")
    if not api_key:
        raise HTTPException(400, "Claude API key not configured")
    body = await request.body()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            content=body,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@app.post("/api/ai/openai")
async def proxy_openai(request: Request):
    settings = read_json(SETTINGS_FILE, {})
    api_key = settings.get("openaiKey", "")
    if not api_key:
        raise HTTPException(400, "OpenAI API key not configured")
    body = await request.body()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            content=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


@app.post("/api/ai/gemini")
async def proxy_gemini(request: Request):
    settings = read_json(SETTINGS_FILE, {})
    api_key = settings.get("geminiKey", "")
    if not api_key:
        raise HTTPException(400, "Gemini API key not configured")
    body = await request.body()
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            content=body,
            headers={"Content-Type": "application/json"},
        )
    return JSONResponse(content=resp.json(), status_code=resp.status_code)


# ── 默认 Prompts ──────────────────────────────────────
DEFAULT_SYSTEM_PROMPT = """你是一名专业的英中翻译，负责将英文科普/理性主义文章翻译成自然流畅的中文。

翻译规范：
1. 人名、软件名、论文名保留英文
2. Markdown 链接括号保持半角 []()，不改为全角
3. 使用中文全角标点，包括英文词汇后面也用全角
4. 中文与英文/数字之间加空格
5. 专有名词用「」，隐喻用""，书名用《》
6. 不对中文使用斜体，改用**粗体**或引号
7. 保持作者原有语气，不要过度学术化

请直接输出译文，不要加任何解释或前言。"""

DEFAULT_PROOFREAD_PROMPT = """你是一名专业的中文译文校对，负责审查英中翻译质量。

校对重点：
1. 对照原文检查是否有漏译、误译、歧义
2. 检查人名/软件名/论文名是否保留英文
3. 检查 Markdown 链接括号是否为半角 []()
4. 检查标点是否使用中文全角
5. 中文与英文/数字之间是否有空格
6. 专有名词是否用「」，书名是否用《》
7. 语言是否自然流畅，有无生硬的学术腔

请指出问题并给出修改后的完整译文。"""


if __name__ == "__main__":
    import uvicorn
    print("🚀 汉化工作台启动中...")
    print("📂 数据目录:", DATA_DIR.absolute())
    print("🌐 访问地址: http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)
