# better singleton pattern
import asyncio
from typing import Dict
from fastapi import WebSocket
from langchain_core.messages import HumanMessage
from agent.core import agent
from e2b_code_interpreter import AsyncSandbox
import os
from dotenv import load_dotenv 
from utils.persistent_store import load_file_store,save_file_store
load_dotenv() 
api_key = os.getenv("E2B_API_KEY")
class AgentService:
    def __init__(self):
        self.agent = agent
        self.sandboxes: Dict[str, AsyncSandbox] = {}

    async def get_sandbox(self, project_id: str):
        if project_id not in self.sandboxes:
            print(f'Initializing new sandbox for project: {project_id}')
            self.sandboxes[project_id] =await  AsyncSandbox.create(timeout=300)
        #     await self.sandboxes[project_id].commands.run("curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && "
        # "apt-get install -y nodejs") 
            exec_result = await self.sandboxes[project_id].commands.run("npm --version", )
            print("----------------------------------")
            print("\n \n")
            print(f"NPM --VERSION result: {exec_result}")
            print("\n \n")
            print("----------------------------------")
            print("Sandbox is setup create with NPM environment")
        return self.sandboxes[project_id]

    async def close_sandbox(self, project_id: str):
        """Close a specific sandbox"""
        if project_id in self.sandboxes:
            await self.sandboxes[project_id].kill()
            del self.sandboxes[project_id]
            print(f'  Closed sandbox: {project_id}')

    async def exec_in_sandbox(self, tool_name: str, tool_args: dict, sandbox: AsyncSandbox, socket: WebSocket):
        # check which tool is being called
        if tool_name == 'create_file':
            file_path = tool_args['file_path']
            content = tool_args['content']
            await sandbox.files.write(file_path, content) 
            if socket:
               await  socket.send_json({'e': 'file_created', 'message': f'Created {file_path}'})
        elif tool_name == "execute_command":
            command = tool_args["command"]
            print(f"command :{command}")
            if socket:
                await socket.send_json({
                    "e":"command_started",
                    "command" : command 
                })
            print(f"received command : {command}")
            execution = await sandbox.commands.run(command)
            result = {
                "command": command,
                # "stdout": execution.logs.stdout,
                # "stderr": execution.logs.stderr,
                "exit_code": 0 if not execution.error else 1
            }

            if socket:
                await socket.send_json({
                    "e": "command_completed",
                    "result": result
                })
            
            return result
        return {}
    
    async def run_agent_stream(self,prompt:str,project_id:str,socket:WebSocket):
        messages = [HumanMessage(content=prompt)]
        sandbox = await self.get_sandbox(project_id)
        file_store = load_file_store(project_id)
        if socket:
            await socket.send_json({
                "e": "started",   
                "message": "Creating project..."
            })
        try:
            async for chunk in self.agent.astream(messages, stream_mode="updates"): 
                if "call_llm" in chunk:
                    llm_msg = chunk["call_llm"]
                    # print(f"LLM_MESSAGE \n {llm_msg}") 
                    # Stream AI thinking
                    if hasattr(llm_msg, "content") and llm_msg.content:
                        if socket:
                            await socket.send_json({
                                "e": "thinking",
                                "content": llm_msg.content
                            })
                    
                    # Handle tool calls
                    if hasattr(llm_msg, "tool_calls") and llm_msg.tool_calls:
                        for call in llm_msg.tool_calls:
                            print(f"Tool Called : {call['name']} \n")
                            tool_name = call["name"]
                            args = call["args"]
                            
                            # Execute in E2B sandbox
                            result = await self.exec_in_sandbox(
                                tool_name,
                                args,
                                sandbox,
                                socket
                            )
                            
                            # Save to persistent store (for your existing logic)
                            if tool_name == "create_file":
                                entry = {
                                    "file_path": args["file_path"],
                                    "content": args["content"]
                                }
                                file_store.append(entry)
                                save_file_store(project_id, file_store)
                            
                            await asyncio.sleep(0.05)
            #install dependency and run project inside the sandbox
            await self.exec_in_sandbox("execute_command",{"command": "npm install"},sandbox,socket) 
            await self.exec_in_sandbox("execute_command",{"command": "npm run dev"},sandbox,socket) 

            if socket:
                await socket.send_json({
                    "e": "completed",
                    "message": "Project Created Successfully",
                    "sandbox_id": sandbox.sandbox_id
                })
        
        except Exception as e:
            print(f"❌ Error: {e}")
            if socket:
                await socket.send_json({
                    "e": "error",
                    "message": str(e)
                })
            raise
    


agent_service = AgentService()
         

