import os
import asyncio
from typing import TypedDict, Annotated, Sequence
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END, add_messages
from langchain_core.messages import SystemMessage, BaseMessage, ToolMessage, AIMessage
from dotenv import load_dotenv
from .tools import create_file, execute_command, get_context, save_context
from prompt import PROMPT
import logging

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


class AgentState(TypedDict):
    """State schema for the agent graph"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    iteration_count: int


def should_continue(state: AgentState) -> str:
    """
    Determine whether to continue with tool calls or end.
    Returns 'continue' if there are tool calls, 'end' otherwise.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if state.get("iteration_count", 0) >= MAX_TOOL_ITERATIONS:
        logger.warning(f"Reached maximum tool iterations ({MAX_TOOL_ITERATIONS})")
        return "end"
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "continue"
    
    return "end"


async def call_llm(state: AgentState) -> AgentState:
    """
    Call the LLM with the current messages.
    """
    messages = state["messages"]
    
    try:
        llm_messages = [SystemMessage(content=PROMPT)] + list(messages)
        response = await llm_with_tools.ainvoke(llm_messages)
        
        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0)
        }
    except Exception as e:
        logger.error(f"Error calling LLM: {e}")
        raise


async def execute_tools(state: AgentState) -> AgentState:
    """
    Execute tool calls from the last AI message.
    Only handles context tools (get_context, save_context).
    Sandbox tools (create_file, execute_command) are handled externally by agent_service.
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return state
    
    iteration_count = state.get("iteration_count", 0) + 1
    tool_names = [tc.get('name', 'unknown') for tc in last_message.tool_calls]
    logger.info(f"Tool call iteration {iteration_count}, tools: {tool_names}")
    
    tool_results = []
    sandbox_tools = ['create_file', 'execute_command']
    
    existing_tool_results = {
        msg.tool_call_id: msg 
        for msg in messages 
        if isinstance(msg, ToolMessage)
    }
    
    for tool_call in last_message.tool_calls:
        tool_name = tool_call.get('name')
        tool_args = tool_call.get('args', {})
        tool_call_id = tool_call.get('id', 'unknown')
        
        if tool_name in sandbox_tools:
            if tool_call_id in existing_tool_results:
                logger.debug(f"Using existing result for sandbox tool {tool_name} from agent_service")
                tool_results.append(existing_tool_results[tool_call_id])
            else:
                logger.debug(f"Skipping sandbox tool {tool_name} - will be handled by agent_service")
                tool_results.append(ToolMessage(
                    content=f"Tool {tool_name} will be executed externally",
                    tool_call_id=tool_call_id
                ))
            continue
        
        if tool_name not in tools_by_name:
            error_msg = f"Unknown tool: {tool_name}. Available tools: {list(tools_by_name.keys())}"
            logger.error(error_msg)
            tool_results.append(ToolMessage(
                content=f"Error: {error_msg}",
                tool_call_id=tool_call_id
            ))
            continue
        
        try:
            tool = tools_by_name[tool_name]
            result = await tool.ainvoke(tool_args)
            
            if not isinstance(result, str):
                result = str(result)
            
            tool_results.append(ToolMessage(
                content=result,
                tool_call_id=tool_call_id
            ))
        except Exception as e:
            error_msg = f"Error executing tool {tool_name}: {str(e)}"
            logger.error(error_msg)
            tool_results.append(ToolMessage(
                content=f"Error: {error_msg}",
                tool_call_id=tool_call_id
            ))
    
    return {
        "messages": [last_message] + tool_results,
        "iteration_count": iteration_count
    }


def create_agent_graph():
    """
    Create and compile the agent StateGraph.
    """
    workflow = StateGraph(AgentState)
    
    workflow.add_node("call_llm", call_llm)
    workflow.add_node("execute_tools", execute_tools)
    
    workflow.set_entry_point("call_llm")
    
    workflow.add_conditional_edges(
        "call_llm",
        should_continue,
        {
            "continue": "execute_tools",
            "end": END
        }
    )
    
    workflow.add_edge("execute_tools", "call_llm")
    
    return workflow.compile()


agent = create_agent_graph()
