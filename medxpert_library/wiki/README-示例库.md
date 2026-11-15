# 示例知识库说明

这是 **MedXpert 图书馆（通用版）连接器** 自带的示例知识库，仅用于演示连接器工作流。

## 如何替换成你自己的知识库

1. 把你自己团队的 `.md` 文档放进 `wiki/` 目录（可建子目录分类）。
2. 安装并启动本地 Ollama，拉取嵌入模型：
   ```
   ollama pull bge-m3
   ```
   如需 `ask_knowledge` 问答能力，再拉取一个生成模型：
   ```
   ollama pull qwen2.5:7b
   ```
3. 构建向量索引：
   ```
   python rag_engine.py build
   ```
4. 启动 MCP server（stdio）：
   ```
   python medxpert_library_server.py
   ```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LIBRARY_WIKI_DIR` | 本包 `wiki/` | 知识库目录 |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 地址 |
| `LIBRARY_EMBED_MODEL` | `bge-m3` | 嵌入模型 |
| `LIBRARY_GEN_MODEL` | `qwen2.5:7b` | 生成模型（问答用） |

> 所有内容均在你本机处理，不上传任何外部服务。
