"""MedXpert Library — local RAG MCP server (stdlib only, offline).

The PyPI distribution ships the same code the repository runs: the stdio
JSON-RPC server, the BM25/cosine RAG engine and a small sample wiki so the
server answers out of the box. Point ``LIBRARY_WIKI_DIR`` at your own
directory of ``.md`` files to search your own knowledge base.
"""

__version__ = "1.0.1"

__all__ = ["__version__"]
