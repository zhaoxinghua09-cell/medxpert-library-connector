#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MedXpert 图书馆 — 通用版 MCP Server（stdio JSON-RPC 2.0，纯标准库实现）
本地知识库语义检索 + RAG 问答。零第三方依赖，仅依赖本地 Ollama 做嵌入/生成；零积分、断网可用。

数据源：用户自己的 wiki 目录（.md），默认指向本包内 wiki/ 示例库。
工具：
  - search_knowledge(query, top_k?)   语义检索知识库（本地嵌入模型 + 余弦）
  - get_page(title)                   读取单个 wiki 页全文
  - list_sources()                    库范围 / 分类 / 索引状态
  - ask_knowledge(question, top_k?)   RAG 问答（检索 + 本地生成模型，附引用）

运行：
  python medxpert_library_server.py            # 作为 MCP server 监听 stdio
  python medxpert_library_server.py --selftest # 离线自测（需先 build 索引）

环境变量：
  LIBRARY_WIKI_DIR    知识库目录（默认：本包 wiki/）
  OLLAMA_BASE_URL     Ollama 地址（默认 http://127.0.0.1:11434）
  LIBRARY_EMBED_MODEL 嵌入模型（默认 bge-m3）
  LIBRARY_GEN_MODEL   生成模型（默认 qwen2.5:7b）
"""
import sys
import os
import json
import time
import urllib.request

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {
    "name": "MedXpert Library",
    "version": "1.0.0",
    "brand": {
        "company": "MedXpert",
        "company_cn": "美达信医疗",
        "product": "MedXpert 图书馆（通用版）",
    },
}

# 复用同包内的 RAG 引擎（embed / cosine / search_results / build）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag_engine as lib  # noqa: E402

WIKI_DIR = lib.WIKI_DIR
OLLAMA = lib.OLLAMA
GEN_MODEL = lib.GEN_MODEL


# ---------- 工具实现 ----------
def tool_search_knowledge(query, top_k=5):
    if not query:
        raise ValueError("query 必填")
    results = lib.search_results(query, k=max(1, min(int(top_k or 5), 20)))
    return {"query": query, "results": results,
            "note": "数据来源：本地知识库（%s 语义检索，零积分）" % lib.EMBED_MODEL}


def tool_get_page(title):
    if not title:
        raise ValueError("title 必填")
    cands = []
    for root, _, files in os.walk(WIKI_DIR):
        if os.path.basename(root) == "rag_index.json":
            continue
        for fn in files:
            if fn.endswith(".md"):
                cands.append(os.path.join(root, fn))

    def match(p, t):
        base = os.path.splitext(os.path.basename(p))[0]
        if base == t:
            return 3
        if t in p:
            return 2
        try:
            with open(p, encoding="utf-8", errors="ignore") as f:
                first = f.readline().strip()
            if first.startswith("#") and first.lstrip("#").strip() == t:
                return 3
        except Exception:
            pass
        return 0

    best = None
    best_score = 0
    for p in cands:
        s = match(p, title)
        if s > best_score:
            best, best_score = p, s
    if not best or best_score == 0:
        raise ValueError("未找到页面: %s（可先 search_knowledge 拿到准确标题）" % title)
    with open(best, encoding="utf-8", errors="ignore") as f:
        content = f.read()
    return {"title": os.path.basename(best), "path": best,
            "content": content[:8000], "chars": len(content)}


def tool_list_sources():
    n = 0
    cats = {}
    for root, _, files in os.walk(WIKI_DIR):
        if os.path.basename(root) == "rag_index.json":
            continue
        for fn in files:
            if fn.endswith(".md"):
                n += 1
                rel = os.path.relpath(root, WIKI_DIR)
                key = rel if rel != "." else "根目录"
                cats[key] = cats.get(key, 0) + 1
    idx_n = 0
    idx_mtime = None
    if os.path.exists(lib.INDEX_PATH):
        try:
            with open(lib.INDEX_PATH, encoding="utf-8") as f:
                idx_n = len(json.load(f))
            idx_mtime = time.ctime(os.path.getmtime(lib.INDEX_PATH))
        except Exception:
            pass
    return {"pages": n, "categories": cats, "rag_index_entries": idx_n,
            "index_updated": idx_mtime, "wiki_dir": WIKI_DIR}


def ollama_chat(prompt, model=GEN_MODEL):
    req = urllib.request.Request(
        OLLAMA + "/api/chat",
        data=json.dumps({"model": model,
                         "messages": [{"role": "user", "content": prompt}],
                         "stream": False}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        d = json.loads(r.read())
    return d["message"]["content"]


def tool_ask_knowledge(question, top_k=5):
    if not question:
        raise ValueError("question 必填")
    results = lib.search_results(question, k=max(1, min(int(top_k or 5), 20)))
    ctx = "\n\n".join("[%s] %s" % (r["type"], r["text"][:400]) for r in results[:5])
    if not ctx.strip():
        return {"answer": "未在知识库检索到相关内容，请换个问法或检查索引。",
                "sources": [], "note": "本地 RAG（%s）" % lib.EMBED_MODEL}
    prompt = (
        "你是一个本地知识库问答助手。请严格基于下面的知识片段回答用户问题；"
        "片段里没有的信息，直接说'未查到'，不要编造。\n\n"
        "【知识片段】\n" + ctx + "\n\n【问题】" + question)
    try:
        answer = ollama_chat(prompt)
    except Exception as e:
        answer = "本地生成模型不可用（需 Ollama %s 运行）: %s" % (GEN_MODEL, e)
    return {"answer": answer,
            "sources": [r["text"][:200] for r in results[:5]],
            "note": "本地 RAG（%s 检索 + %s 生成，零积分）" % (lib.EMBED_MODEL, GEN_MODEL)}


# ---------- MCP 协议层 ----------
TOOLS = [
    {
        "name": "search_knowledge",
        "description": "语义检索本地知识库（wiki .md 文档）。返回相关片段及相似度。例：'二类注册需提交哪些资料'、'ISO 13485 现行版本'。",
        "inputSchema": {
            "type": "object",
            "required": ["query"],
            "properties": {
                "query": {"type": "string", "description": "查询内容"},
                "top_k": {"type": "number", "description": "返回条数（1-20，默认 5）"},
            },
        },
    },
    {
        "name": "get_page",
        "description": "读取知识库单个 wiki 页全文。标题可用 search_knowledge 的结果或文件名。",
        "inputSchema": {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string", "description": "页面标题或文件名（不含 .md）"}},
        },
    },
    {
        "name": "list_sources",
        "description": "返回知识库范围：页数、分类统计、RAG 索引条目数、数据源目录。",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "ask_knowledge",
        "description": "RAG 问答：检索知识库片段 + 本地生成模型回答，附引用来源。零积分、离线可用。",
        "inputSchema": {
            "type": "object",
            "required": ["question"],
            "properties": {
                "question": {"type": "string", "description": "向知识库提问"},
                "top_k": {"type": "number", "description": "检索片段数（默认 5）"},
            },
        },
    },
]


def dispatch_tool(name, args):
    args = args or {}
    if name == "search_knowledge":
        res = tool_search_knowledge(args.get("query"), args.get("top_k", 5))
        return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}],
                "structuredContent": {"knowledge": res}}
    if name == "get_page":
        res = tool_get_page(args.get("title"))
        return {"content": [{"type": "text", "text": res["content"]}],
                "structuredContent": {"page": {k: res[k] for k in ("title", "path", "chars")}}}
    if name == "list_sources":
        res = tool_list_sources()
        return {"content": [{"type": "text", "text": json.dumps(res, ensure_ascii=False)}],
                "structuredContent": {"sources": res}}
    if name == "ask_knowledge":
        res = tool_ask_knowledge(args.get("question"), args.get("top_k", 5))
        return {"content": [{"type": "text", "text": res["answer"]}],
                "structuredContent": {"answer": res}}
    raise ValueError("未知工具: %s" % name)


def make_response(msg_id, result):
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def make_error(msg_id, code, message):
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def handle(msg):
    method = msg.get("method")
    msg_id = msg.get("id")
    params = msg.get("params", {}) or {}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "ping":
        return make_response(msg_id, {})
    if method == "initialize":
        return make_response(msg_id, {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": SERVER_INFO})
    if method == "tools/list":
        return make_response(msg_id, {"tools": TOOLS})
    if method == "tools/call":
        try:
            res = dispatch_tool(params.get("name"), params.get("arguments"))
            return make_response(msg_id, res)
        except Exception as e:
            return make_response(msg_id, {
                "content": [{"type": "text", "text": "错误: %s" % e}],
                "isError": True})
    return make_error(msg_id, -32601, "方法不存在: %s" % method)


def serve():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue
        out = handle(msg)
        if out is not None:
            sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
            sys.stdout.flush()


# ---------- 离线自测 ----------
def selftest():
    print("=== MedXpert 图书馆 MCP Server 离线自测（通用版）===")
    b = SERVER_INFO["brand"]
    print("[品牌] %s（%s）| 产品：%s" % (b["company"], b["company_cn"], b["product"]))
    r = handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    print("[initialize]", r["result"]["serverInfo"]["name"], "v" + r["result"]["serverInfo"]["version"])
    r = handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    print("[tools/list]", [t["name"] for t in r["result"]["tools"]])
    r = handle({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                "params": {"name": "list_sources", "arguments": {}}})
    src = r["result"]["structuredContent"]["sources"]
    print("[list_sources] 页数=%s 分类=%s 索引条目=%s" % (
        src["pages"], list(src["categories"].keys()), src["rag_index_entries"]))
    r = handle({"jsonrpc": "2.0", "id": 4, "method": "tools/call",
                "params": {"name": "search_knowledge",
                           "arguments": {"query": "如何使用本知识库", "top_k": 3}}})
    kn = r["result"]["structuredContent"]["knowledge"]
    print("[search_knowledge] 命中 %d 条，首条: %s" % (
        len(kn["results"]), kn["results"][0]["text"][:50] if kn["results"] else "无"))
    print("=== 自测通过（检索需先 `python rag_engine.py build`）===")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        serve()
