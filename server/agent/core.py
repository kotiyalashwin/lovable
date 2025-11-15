import os
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import add_messages
from langchain_core.messages import SystemMessage, BaseMessage, ToolCall, ToolMessage, AIMessage
from langgraph.func import entrypoint, task
from dotenv import load_dotenv
from .tools import create_file, execute_command, get_context, save_context
from prompt import PROMPT
import logging
from typing import cast, Any

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
if api_key is None:
    raise Exception('API key not found')

logger = logging.getLogger(__name__)

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=api_key)

tools = [create_file, execute_command, save_context, get_context]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)

# Maximum number of tool call iterations to prevent infinite loops
MAX_TOOL_ITERATIONS = 50


@task
async def call_llm(messages: list[BaseMessage]):
    """LLM decides whether to call a tool or not"""
    try:
        response = await llm_with_tools.ainvoke([SystemMessage(content=PROMPT)] + messages)
        return response
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


@task
async def call_tool(tool_call: ToolCall):
    """Performs the tool call with error handling."""
    tool_name = tool_call.get('name')
    tool_args = tool_call.get('args', {})
    
    if tool_name not in tools_by_name:
        error_msg = f"Unknown tool: {tool_name}. Available tools: {list(tools_by_name.keys())}"
        logger.error(error_msg)
        return ToolMessage(
            content=f"Error: {error_msg}",
            tool_call_id=tool_call.get('id', 'unknown')
        )
    
    try:
        tool = tools_by_name[tool_name]
        result = await tool.ainvoke(tool_args)
        
        # Ensure result is a string for ToolMessage
        if not isinstance(result, str):
            result = str(result)
            
        return ToolMessage(
            content=result,
            tool_call_id=tool_call.get('id', 'unknown')
        )
    except Exception as e:
        error_msg = f"Error executing tool {tool_name}: {str(e)}"
        logger.error(error_msg)
        return ToolMessage(
            content=f"Error: {error_msg}",
            tool_call_id=tool_call.get('id', 'unknown')
        )


@entrypoint()
async def agent(messages: list[BaseMessage]):
    """
    Main agent loop that handles LLM calls and tool execution.
    Includes iteration limit to prevent infinite loops.
    """
    llm_response = await call_llm(messages)
    iteration_count = 0

    while isinstance(llm_response, AIMessage) and llm_response.tool_calls and iteration_count < MAX_TOOL_ITERATIONS:
        iteration_count += 1
        tool_names = [tc.get('name', 'unknown') for tc in llm_response.tool_calls]
        logger.info(f"Tool call iteration {iteration_count}, tools: {tool_names}")
        tool_result_futures = [call_tool(tc) for tc in llm_response.tool_calls]
        tool_results = await asyncio.gather(*tool_result_futures)

        messages_to_add: Any = [llm_response, *tool_results]
        messages = cast(list[BaseMessage], list(add_messages(cast(Any, messages), messages_to_add)))
        
        llm_response = await call_llm(messages)

    if iteration_count >= MAX_TOOL_ITERATIONS:
        logger.warning(f"Reached maximum tool iterations ({MAX_TOOL_ITERATIONS})")
        warning_msg = ToolMessage(
            content=f"Warning: Reached maximum tool call iterations ({MAX_TOOL_ITERATIONS}). Stopping to prevent infinite loop.",
            tool_call_id="system"
        )
        warning_messages: Any = [warning_msg]
        messages = cast(list[BaseMessage], list(add_messages(cast(Any, messages), warning_messages)))

    
    final_messages: Any = [llm_response]
    messages = cast(list[BaseMessage], list(add_messages(cast(Any, messages), final_messages)))
    return messages
