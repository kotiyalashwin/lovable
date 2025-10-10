import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import add_messages
from langchain_core.messages import SystemMessage, BaseMessage, ToolCall
from langgraph.func import entrypoint, task
from dotenv import load_dotenv
from .tools import create_file, execute_command

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY')
if api_key is None:
    raise Exception('API key not found')

llm = ChatGoogleGenerativeAI(model='gemini-2.5-flash', google_api_key=api_key)

tools = [create_file, execute_command]
tools_by_name = {tool.name: tool for tool in tools}
llm_with_tools = llm.bind_tools(tools)


@task
async def call_llm(messages: list[BaseMessage]):
    """LLM decides whether to call a tool or not"""
    return await llm_with_tools.ainvoke(
        [
            SystemMessage(
                content="""You are Lovable, an agent-based website builder. 
Your job:
- When creating new file provide the file_path and content of that file for the function call
- Createfrontend projects using React + Vite
- Use Tailwind CSS and shadcn/ui for styling
- Deliver all file paths with their content
- Create a README.md with setup and run commands
- Organize files properly (src/, public/, etc.) 
File structure example:
- package.json (with dependencies)
- vite.config.js
- index.html
- src/App.jsx
- src/main.jsx
- src/index.css
- README.md
CRITICAL: Always create vite.config.js with this EXACT configuration:

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    strictPort: true
  }
})
```
Always create complete, runnable projects!"""
            )
        ]
        + messages
    )


@task
async def call_tool(tool_call: ToolCall):
    """Performs the tool call."""
    tool = tools_by_name[tool_call['name']]
    return await tool.ainvoke(tool_call)


@entrypoint()
async def agent(messages: list[BaseMessage]):
    llm_response = await call_llm(messages)

    while True:
        if not llm_response.tool_calls:
            break

        # Process tools and await results
        tool_result_futures = [call_tool(tc) for tc in llm_response.tool_calls]
        tool_results = [await f for f in tool_result_futures]  # Use await

        messages = add_messages(messages, [llm_response, *tool_results])
        llm_response = await call_llm(messages)  # Use await

    messages = add_messages(messages, llm_response)
    return messages
