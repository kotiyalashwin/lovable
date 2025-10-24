# better singleton pattern
import asyncio
from pathlib import Path
from typing import Dict
from fastapi import WebSocket
from langchain_core.messages import HumanMessage
from agent.core import agent
from e2b_code_interpreter import AsyncSandbox
import os
from dotenv import load_dotenv
import json
from utils.persistent_store import load_file_store, save_file_store

load_dotenv()
api_key = os.getenv('E2B_API_KEY')


class AgentService:
    def __init__(self):
        self.agent = agent
        self.sandboxes: Dict[str, AsyncSandbox] = {}

    async def get_sandbox(self, project_id: str):
        if project_id not in self.sandboxes:
            print(f'Initializing new sandbox for project: {project_id}')
            self.sandboxes[project_id] = await AsyncSandbox.create('temp-react', timeout=600)
            print('Sandbox is setup create with REACT environment')
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
            full_path = f'/home/user/react-app/{file_path}'
            await sandbox.files.write(full_path, content)
            if socket:
                await socket.send_json({'e': 'file_created', 'message': f'{file_path}'})

        elif tool_name == 'execute_command':
            command = tool_args['command']
            print(command)
            # TODO: send some better message to the user about executing command
            if socket:
                await socket.send_json({'e': 'command', 'message': command[:200]})

            try:
                # TODO: try and use 'cwd' in run() instead of 'cd' in full_command
                full_command = f'cd /home/user/react-app && {command}'
                result_obj = await sandbox.commands.run(full_command)

                # Log output to console
                print('=' * 60)
                print('✅ Command completed')
                print('=' * 60)
                print('STDOUT:')
                print(result_obj.stdout)
                if result_obj.stderr:
                    print('\nSTDERR:')
                    print(result_obj.stderr)
                print('=' * 60)

                result = {
                    'command': command,
                    'stdout': result_obj.stdout,
                    'stderr': result_obj.stderr,
                    'exit_code': result_obj.exit_code,
                }

                # Check for errors
                if result_obj.exit_code != 0:
                    print(f'⚠️ Command exited with code {result_obj.exit_code}')
                    if socket:
                        await socket.send_json(
                            {'e': 'command_failed', 'error': result_obj.stderr, 'exit_code': result_obj.exit_code}
                        )
                    raise Exception(f'Command failed: {result_obj.stderr}')

                return result

            except Exception as e:
                print(f'❌ Command execution failed: {e}')
                if socket:
                    await socket.send_json({'e': 'command_error', 'error': str(e)})
                raise
        return {}

    async def run_agent_stream(self, prompt: str, project_id: str, socket: WebSocket):
        messages = [HumanMessage(content=prompt)]
        sandbox = await self.get_sandbox(project_id)
        file_store = load_file_store(project_id)
        if socket:
            await socket.send_json({'e': 'started', 'message': 'Creating project...'})
        try:
            async for chunk in self.agent.astream(messages, stream_mode='updates'):
                # print(f"LLM_MESSAGE \n {llm_msg}")
                # print(chunk)
                if 'call_llm' in chunk:
                    llm_msg = chunk['call_llm']
                    # Stream AI thinking
                    if hasattr(llm_msg, 'content') and llm_msg.content:
                        if socket:
                            await socket.send_json({'e': 'thinking', 'message': llm_msg.content})

                    # Handle tool calls
                    if hasattr(llm_msg, 'tool_calls') and llm_msg.tool_calls:
                        for call in llm_msg.tool_calls:
                            print(f'Tool Called : {call["name"]} \n')
                            tool_name = call['name']
                            args = call['args']
                            if tool_name == 'get_context':
                                try:
                                    context_path = Path(f'data/project/{project_id}/context/context.json')

                                    if not context_path.exists():
                                        messages.append(HumanMessage(content='No Context this is a fresh project'))

                                    with open(context_path, 'r', encoding='utf-8') as f:
                                        context = json.load(f)

                                    messages.append(
                                        HumanMessage(
                                            content=f'Also here is the context of what you did before CONTEXT: {context}'
                                        )
                                    )
                                    continue
                                except Exception as e:
                                    print(f'Erorr getting context \n {e}')
                            if tool_name == 'save_context':
                                base_dir = Path(f'data/project/{project_id}')
                                context_dir = base_dir / 'context'
                                semantic = args['semantic']
                                procedural = args['procedural']
                                episodic = args['episodic']
                                try:
                                    file_store = load_file_store(project_id)
                                    code_map = {entry['file_path']: entry['content'] for entry in file_store}
                                    os.makedirs(context_dir, exist_ok=True)
                                    context_data = {
                                        'semantic': semantic.strip(),
                                        'procedural': procedural.strip(),
                                        'episodic': episodic.strip(),
                                        'code_map': code_map,
                                        'structue': list(code_map.keys()),
                                    }

                                    context_path = os.path.join(context_dir, 'context.json')
                                    with open(context_path, 'w') as f:
                                        json.dump(
                                            context_data,
                                            f,
                                            indent=2,
                                        )
                                    print('Successfully save context for this command')
                                    continue
                                except Exception as e:
                                    print(f'Error(Failed to save context) \n {e}')

                            # Execute in E2B sandbox
                            result = await self.exec_in_sandbox(
                                tool_name,
                                args,
                                sandbox,
                                socket,
                            )
                            # Save to persistent store (for your existing logic)
                            if tool_name == 'create_file':
                                entry = {'file_path': args['file_path'], 'content': args['content']}
                                file_store.append(entry)
                                save_file_store(project_id, file_store)

                            await asyncio.sleep(0.05)
            # Build
            host = sandbox.get_host(5173)
            url = f'https://{host}'

            print(f'\n🌐 Project live at: {url}\n')

            if socket:
                await socket.send_json(
                    {'e': 'completed', 'message': 'Project Created Successfully', 'sandbox_id': sandbox.sandbox_id}
                )

        except Exception as e:
            print(f'❌ Error: {e}')
            if socket:
                await socket.send_json({'e': 'error', 'message': str(e)})
            raise


agent_service = AgentService()
