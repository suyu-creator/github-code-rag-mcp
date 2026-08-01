"""MCP server entry point. Uses same pattern as vision-server (stdio_server + asyncio)."""
import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.mcp_server import mcp, _init_engine


async def main():
    data_dir = os.environ.get("CODE_RAG_DATA_DIR", os.path.expanduser("~/.code-rag"))
    _init_engine(data_dir)

    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await mcp._mcp_server.run(
            read_stream,
            write_stream,
            mcp._mcp_server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())