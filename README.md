# MedXpert 图书馆（通用版）连接器

把**你自己的 wiki（.md 文档）**做成可语义检索、可 RAG 问答的本地知识库 MCP 连接器。

- 纯 Python 标准库实现（stdio JSON-RPC 2.0），**零第三方依赖**
- 仅依赖**本地 Ollama** 做嵌入/生成，**零积分、断网可用**
- 知识库为你自有文档，连接器不绑定任何预置私有数据
- 全部计算在本机完成，不访问任何外部网络，不上传任何数据

## 工具

| 工具 | 说明 |
|------|------|
| `search_knowledge(query, top_k?)` | 语义检索知识库，返回相关片段 + 相似度 |
| `get_page(title)` | 读取单个 wiki 页全文 |
| `list_sources()` | 库范围：页数 / 分类 / 索引状态 |
| `ask_knowledge(question, top_k?)` | RAG 问答：检索 + 本地生成模型，附引用 |

## 快速开始

```bash
# 1. 安装并启动 Ollama，拉取模型
ollama pull bge-m3            # 检索必备（嵌入）
ollama pull qwen2.5:7b        # 问答可选（生成）

# 2. 用你自己的文档替换 wiki/（本包自带 3 个示例页）
#    把 .md 放进 wiki/ 即可，可建子目录分类

# 3. 构建向量索引
python rag_engine.py build

# 4. 启动 MCP server（stdio）
python medxpert_library_server.py
```

## 接入 WorkBuddy

包内 `mcp.json` 已提供标准配置；在开放平台或客户端中引用本包目录即可。
也可用环境变量覆盖默认行为：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LIBRARY_WIKI_DIR` | 本包 `wiki/` | 知识库目录（指向你的文档） |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Ollama 地址 |
| `LIBRARY_EMBED_MODEL` | `bge-m3` | 嵌入模型 |
| `LIBRARY_GEN_MODEL` | `qwen2.5:7b` | 生成模型（问答） |

## 包结构

```
medxpert-library-connector/
├── medxpert_library_server.py   # MCP server（stdio，纯标准库）
├── rag_engine.py                # 嵌入 / 余弦 / 构建 / 检索引擎
├── wiki/                        # 示例知识库（替换成你自己的 .md）
├── connector-meta.json          # 开放平台元数据
├── mcp.json                     # MCP 启动配置
├── icon.svg                     # 头像
├── LICENSE                  # Apache-2.0
├── requirements.txt             # 依赖说明（仅 Ollama）
└── README.md
```

## 合规与隐私

- 不内嵌受版权保护的标准正文，仅索引标准号与公开要点。
- 所有内容在本机处理，文档与查询均不上传外部服务。
- 知识库为使用者自有内容，发布者不对其内容负责。

---

## 许可说明 · License Notice

- **代码许可**：本仓库源代码以 **Apache-2.0** 许可发布（见根目录 [LICENSE](LICENSE)），版权归「赵兴华 / Steven Zhao·China（ORCID 0009-0001-0512-1237）」。
- **内容权属**：本仓库不捆绑专有知识库；随附示例内容仅供演示，归其原始所有者所有。代码以 Apache-2.0 许可发布。
- **品牌状态限定**：MedXpert、SynomosAI、LGD 等为相关项目标识，**均未申请实体注册、未申请商标注册**；出现仅作来源标识，不构成对法人实体或商标权的任何主张。
- **免责**：本仓库内容不构成法规意见、法律意见或注册代理服务；关键数据以监管机构最新发布为准。
- **联系**：zhaoxinghua09@gmail.com ｜ ORCID 0009-0001-0512-1237

`mcp-name: io.github.zhaoxinghua09-cell/medxpert-library-connector`
