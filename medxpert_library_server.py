#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""源文件入口（保留原命令行用法）：

    python medxpert_library_server.py             # MCP stdio server
    python medxpert_library_server.py --selftest  # 离线自测

实现在 `medxpert_library` 包内（medxpert_library/server.py），PyPI 分发版与
源码树跑的是同一份代码；本文件只做转发。
"""
import sys

from medxpert_library.server import main

if __name__ == "__main__":
    sys.exit(main())
