async def read_list(mcp_client, tool_name):
    result = await mcp_client.call_tool(tool_name, {})

    if result.is_error:
        message = result.content[0].text
        return None, f"Could not read {tool_name}: {message}"

    return result.structured_content["result"], None