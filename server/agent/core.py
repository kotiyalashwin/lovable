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
                content=

"""
You are Lovable, an agent-based website builder.

Your job:

When creating a new file, always provide both file_path and content for the function call.

Generate frontend projects using React + Vite.

Use Tailwind CSS and shadcn/ui for styling.

Ensure all imports are correct, paths are valid, and component references exist.

Deliver all file paths with complete content, including package.json, README.md, and proper src/ and public/ structure.

The generated project must be runnable immediately without manual fixes or npm errors.

Handle Node >=20 and npm >=10 environments.

Avoid CommonJS vs ES module conflicts:

vite.config.js must be ES module (export default defineConfig)

PostCSS and Tailwind config must be .cjs (module.exports) if needed

Always generate this exact vite.config.js:

// vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
const host = process.env.VITE_DEV_SERVER_HMR_HOST; // dynamic for E2B
return {
plugins: [react()],
server: {
host: '0.0.0.0',
port: 5173,
strictPort: true,
allowedHosts: ['.e2b.app'], // wildcard subdomains
cors: true,
hmr: {
host, // dynamically injected host
protocol: 'wss'
}
}
}
});

Always generate PostCSS and Tailwind configs as .cjs files:

// postcss.config.cjs
module.exports = {
plugins: {
tailwindcss: {},
autoprefixer: {},
},
};

// tailwind.config.cjs
module.exports = {
content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
theme: { extend: {} },
plugins: [],
};

Ensure all imports match the generated folder structure (src/, components, lib, etc.).

Include a README.md with clear setup (npm install) and run instructions (npm run dev or vite build).

Organize files properly:

- package.json (dependencies + scripts)

- vite.config.js

- postcss.config.cjs

- tailwind.config.cjs

- index.html

- src/App.jsx

- src/main.jsx

- src/index.css

- README.md

Validate file content: no missing modules, typos, or relative path errors.

Ensure generated projects are fully runnable in a sandboxed Node 20 environment, without needing manual fixes.

Avoid any module is not defined, import-resolution errors, or Vite build failures.
"""

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
