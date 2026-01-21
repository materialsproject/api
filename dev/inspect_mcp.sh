#!/bin/bash -l

# Tool to run the MCP inspector:
# https://modelcontextprotocol.io/docs/tools/inspector

server_path=$(python -c 'from importlib_resources import files ; print(str((files("mp_api.client") / ".."/ "..").resolve()))')

fastmcp dev \
    --python 3.12 \
    --with-editable $server_path \
    --with-requirements "$server_path/requirements/requirements-ubuntu-latest_py3.12_extras.txt" \
    "$server_path/mp_api/mcp/server.py"
