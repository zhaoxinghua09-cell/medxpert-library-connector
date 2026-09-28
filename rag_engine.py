# -*- coding: utf-8 -*-
"""
MedXpert 本地知识库 RAG 引擎（通用版，零第三方依赖）
- 数据源：用户自己的 wiki 目录（.md 全文），默认指向本包内 wiki/ 示例库
- 嵌入：本地 Ollama 嵌入模型（默认 bge-m3，1024 维，中文友好）
- 检索：余弦相似度 top-k
- 仅依赖 Python 标准库 + 本地 Ollama，零积分、断网可用

用法：
  python rag_engine.py build                  # 构建/重建向量索引（需先装 Ollama 并 pull 嵌入模型）
  python rag_engine.py search "查询内容" --k 5  # 检索

所有路径/模型均可用环境变量覆盖：
  LIBRARY_WIKI_DIR    知识库目录（默认：本包 wiki/）
  OLLAMA_BASE_URL     Ollama 地址（默认 http://127.0.0.1:11434）
  LIBRARY_EMBED_MODEL 嵌入模型（默认 bge-m3）
  LIBRARY_GEN_MODEL   生成模型（默认 qwen2.5:7b，仅 ask 问答用）
"""
import os
import sys
import json
import math
import urllib.request

# ---------- 可配置项（环境变量优先，默认指向包内示例库） ----------
OLLAMA = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
EMBED_MODEL = os.environ.get("LIBRARY_EMBED_MODEL", "bge-m3")
GEN_MODEL = os.environ.get("LIBRARY_GEN_MODEL", "qwen2.5:7b")

_PKG_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_DIR = os.environ.get("LIBRARY_WIKI_DIR", os.path.join(_PKG_DIR, "wiki"))
INDEX_PATH = os.path.join(WIKI_DIR, "rag_index.json")


def embed(text):
    """调用本地 Ollama 嵌入接口，返回向量列表。"""
    req = urllib.request.Request(
        OLLAMA + "/api/embed",
        data=json.dumps({"model": EMBED_MODEL, "input": text}).encode(),
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
    return d["embeddings"][0]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def collect_items():
    """收集知识库条目：遍历 WIKI_DIR 下所有 .md（除索引文件）。"""
    items = []
    if not os.path.isdir(WIKI_DIR):
        print("⚠️ 知识库目录不存在: %s（请设置 LIBRARY_WIKI_DIR 或放入 wiki/）" % WIKI_DIR)
        return items
    md_seen = set()
    for root, _, files in os.walk(WIKI_DIR):
        if os.path.basename(root) == "rag_index.json" or "rag_index.json" in root:
            continue
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(root, fn)
            if p in md_seen:
                continue
            md_seen.add(p)
            try:
                with open(p, encoding="utf-8", errors="ignore") as f:
                    content = f.read(4000)
            except Exception:
                content = ""
            rel = os.path.relpath(p, WIKI_DIR)
            items.append({"text": rel + "：" + content.strip()[:800], "type": "知识"})
    return items


def build():
    """构建向量索引并落盘 rag_index.json。"""
    items = collect_items()
    if not items:
        print("❌ 知识库为空，未生成索引。请先放入 .md 文档到: %s" % WIKI_DIR)
        return
    print("索引 %d 项，嵌入中（%s 本地）..." % (len(items), EMBED_MODEL))
    index = []
    for i, it in enumerate(items):
        vec = embed(it["text"][:400])
        index.append({"text": it["text"], "type": it["type"], "vec": vec})
        if (i + 1) % 50 == 0:
            print("  %d/%d" % (i + 1, len(items)))
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)
    print("✅ 索引保存: %s" % INDEX_PATH)


def search_results(query, k=5):
    """返回结构化检索结果（供 MCP server 调用）。"""
    if not os.path.exists(INDEX_PATH):
        raise FileNotFoundError(
            "RAG 索引不存在，请先运行 `python rag_engine.py build`（需本地 Ollama + 嵌入模型 %s）" % EMBED_MODEL)
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    qv = embed(query[:400])
    scored = [(cosine(qv, it["vec"]), it) for it in index]
    scored.sort(key=lambda x: -x[0])
    return [
        {"type": it["type"], "score": round(s, 3), "text": it["text"][:500]}
        for s, it in scored[:k]
    ]


def search(query, k=5):
    """命令行检索（打印）。"""
    if not os.path.exists(INDEX_PATH):
        print("索引不存在，先运行 build")
        return
    with open(INDEX_PATH, encoding="utf-8") as f:
        index = json.load(f)
    qv = embed(query[:400])
    scored = [(cosine(qv, it["vec"]), it) for it in index]
    scored.sort(key=lambda x: -x[0])
    print("查询: %s\n" % query)
    for i, (s, it) in enumerate(scored[:k], 1):
        print("%d. [%s] 相似度 %.3f" % (i, it["type"], s))
        print("   %s" % it["text"][:120])
        print()


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "build":
        build()
    elif args and args[0] == "search":
        q = args[1] if len(args) > 1 else "示例"
        k = 5
        if "--k" in args:
            k = int(args[args.index("--k") + 1])
        search(q, k)
    else:
        print("用法: build | search 'query' [--k N]")
