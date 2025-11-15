import asyncio
from pathlib import Path
from typing import Dict, Optional
from fastapi import WebSocket
from agent.core import agent
from e2b_code_interpreter import AsyncSandbox
import os
from dotenv import load_dotenv
import json
from utils.persistent_store import load_file_store, save_file_store
import logging

load_dotenv()
api_key = os.getenv('E2B_API_KEY')

logger = logging.getLogger(__name__)


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

    async def exec_in_sandbox(
        self, tool_name: str, tool_args: dict, sandbox: AsyncSandbox, socket: Optional[WebSocket] = None
    ) -> str:
        """
        Execute a tool in the E2B sandbox and return a formatted result string.

        Returns:
            A string result that will be used as the tool result message for the LLM.
        """
        try:
            if tool_name == 'create_file':
                file_path = tool_args.get('file_path')
                content = tool_args.get('content', '')
                if not file_path:
                    error_msg = 'Error: file_path is required for create_file'
                    logger.error(error_msg)
                    await self._send_ws_message(socket, {'e': 'error', 'message': error_msg})
                    return error_msg
                await self._send_ws_message(socket, {'e': 'file_creating', 'message': f'Creating {file_path}...'})

                full_path = f'/home/user/react-app/{file_path}'
                await sandbox.files.write(full_path, content)

                success_msg = f'Successfully created file: {file_path} ({len(content)} characters)'
                logger.info(success_msg)

                await self._send_ws_message(socket, {'e': 'file_created', 'message': file_path})

                return success_msg

            elif tool_name == 'execute_command':
                command = tool_args.get('command', '')

                if not command:
                    error_msg = 'Error: command is required for execute_command'
                    logger.error(error_msg)
                    await self._send_ws_message(socket, {'e': 'error', 'message': error_msg})
                    return error_msg

                logger.info(f'Executing command: {command}')

                await self._send_ws_message(
                    socket,
                    {'e': 'command', 'message': f'Running: {command[:100]}{"..." if len(command) > 100 else ""}'},
                )

                try:
                    full_command = f'cd /home/user/react-app && {command}'
                    result_obj = await sandbox.commands.run(full_command)

                    logger.info('=' * 60)
                    logger.info('✅ Command completed')
                    logger.info('=' * 60)
                    logger.info(f'STDOUT:\n{result_obj.stdout}')
                    if result_obj.stderr:
                        logger.info(f'\nSTDERR:\n{result_obj.stderr}')
                    logger.info('=' * 60)

                    result_parts = [f'Command: {command}']
                    result_parts.append(f'Exit code: {result_obj.exit_code}')

                    if result_obj.stdout:
                        result_parts.append(f'Output:\n{result_obj.stdout}')

                    if result_obj.stderr:
                        result_parts.append(f'Errors:\n{result_obj.stderr}')

                    result_msg = '\n'.join(result_parts)

                    if result_obj.exit_code != 0:
                        warning = f'⚠️ Command exited with code {result_obj.exit_code}'
                        logger.warning(warning)
                        await self._send_ws_message(
                            socket,
                            {
                                'e': 'command_failed',
                                'error': result_obj.stderr or 'Command failed',
                                'exit_code': result_obj.exit_code,
                            },
                        )
                        return f'Command failed with exit code {result_obj.exit_code}:\n{result_msg}'

                    return result_msg

                except Exception as e:
                    error_msg = f'❌ Command execution failed: {e}'
                    logger.error(error_msg)
                    await self._send_ws_message(socket, {'e': 'command_error', 'error': str(e)})
                    return f'Error executing command: {str(e)}'

            else:
                error_msg = f'Unknown tool: {tool_name}'
                logger.error(error_msg)
                return error_msg

        except Exception as e:
            error_msg = f'Error in exec_in_sandbox for {tool_name}: {str(e)}'
            logger.error(error_msg, exc_info=True)
            await self._send_ws_message(socket, {'e': 'error', 'message': error_msg})
            return error_msg

    async def handle_context_tool(
        self, tool_name: str, args: dict, project_id: str, file_store: list
    ) -> Optional[str]:
        """
        Handle context-related tools (get_context, save_context).
        Returns the result message or None if tool was handled internally.
        """
        if tool_name == 'get_context':
            try:
                context_path = Path(f'data/project/{project_id}/context/context.json')

                if not context_path.exists():
                    return 'No context found - this is a fresh project. You can proceed with creating the project from scratch.'

                with open(context_path, 'r', encoding='utf-8') as f:
                    context = json.load(f)

                context_msg = f"""Previous project context:
Semantic: {context.get('semantic', 'N/A')}
Procedural: {context.get('procedural', 'N/A')}
Episodic: {context.get('episodic', 'N/A')}
Existing files: {', '.join(context.get('structue', []))}

Please use this context to understand what was built previously and continue from there."""

                logger.info('Retrieved context for project')
                return context_msg

            except Exception as e:
                error_msg = f'Error getting context: {e}'
                logger.error(error_msg, exc_info=True)
                return f'Error retrieving context: {str(e)}'

        elif tool_name == 'save_context':
            try:
                base_dir = Path(f'data/project/{project_id}')
                context_dir = base_dir / 'context'
                semantic = args.get('semantic', '').strip()
                procedural = args.get('procedural', '').strip()
                episodic = args.get('episodic', '').strip()

                if not semantic:
                    return 'Error: semantic context is required for save_context'

                file_store = load_file_store(project_id)
                code_map = {entry['file_path']: entry['content'] for entry in file_store}

                os.makedirs(context_dir, exist_ok=True)
                context_data = {
                    'semantic': semantic,
                    'procedural': procedural,
                    'episodic': episodic,
                    'code_map': code_map,
                    'structue': list(code_map.keys()),
                }

                context_path = context_dir / 'context.json'
                with open(context_path, 'w', encoding='utf-8') as f:
                    json.dump(context_data, f, indent=2)

                logger.info(f'Successfully saved context for project {project_id}')
                return f'Context saved successfully. Semantic: {semantic[:100]}...'

            except Exception as e:
                error_msg = f'Error saving context: {e}'
                logger.error(error_msg, exc_info=True)
                return f'Error saving context: {str(e)}'

        return None

    async def _send_ws_message(self, socket: Optional[WebSocket], message: dict):
        """Helper to send WebSocket message with immediate flushing"""
        if socket:
            try:
                await socket.send_json(message)
                await asyncio.sleep(0.02)
            except Exception as e:
                logger.warning(f'Failed to send WebSocket message: {e}')

    async def run_agent_stream(self, prompt: str, project_id: str, socket: Optional[WebSocket] = None):
        """
        Run the agent with streaming support, properly handling tool execution
        and feeding results back to the LLM. Messages are sent in real-time.
        Uses StateGraph for better streaming control.
        """
        from langchain_core.messages import HumanMessage, ToolMessage
        from agent.core import AgentState

        current_state: AgentState = {'messages': [HumanMessage(content=prompt)], 'iteration_count': 0}

        sandbox = await self.get_sandbox(project_id)
        file_store = load_file_store(project_id)

        await self._send_ws_message(socket, {'e': 'started', 'message': 'Creating project...'})

        try:
            async for chunk in self.agent.astream(current_state, stream_mode='updates'):  # type: ignore
                if 'call_llm' in chunk:
                    llm_node_output = chunk['call_llm']
                    new_messages = llm_node_output.get('messages', [])

                    if new_messages:
                        current_state['messages'] = list(current_state['messages']) + new_messages
                        llm_msg = new_messages[-1]

                        if hasattr(llm_msg, 'content') and llm_msg.content:
                            await self._send_ws_message(socket, {'e': 'thinking', 'message': llm_msg.content})
                            logger.debug(f'LLM content: {llm_msg.content[:100]}...')

                        if hasattr(llm_msg, 'tool_calls') and llm_msg.tool_calls:
                            sandbox_tool_results = []
                            context_tool_calls = []

                            for call in llm_msg.tool_calls:
                                tool_name = call.get('name', '')

                                if tool_name in ['create_file', 'execute_command']:
                                    args = call.get('args', {})
                                    tool_call_id = call.get('id', 'unknown')

                                    logger.info(f'Executing sandbox tool: {tool_name} with args: {list(args.keys())}')

                                    try:
                                        result_content = await self.exec_in_sandbox(tool_name, args, sandbox, socket)

                                        if tool_name == 'create_file':
                                            entry = {
                                                'file_path': args.get('file_path'),
                                                'content': args.get('content', ''),
                                            }
                                            file_store.append(entry)
                                            save_file_store(project_id, file_store)

                                        sandbox_tool_results.append(
                                            ToolMessage(content=result_content, tool_call_id=tool_call_id)
                                        )

                                    except Exception as e:
                                        error_msg = f'Error executing {tool_name}: {str(e)}'
                                        logger.error(error_msg, exc_info=True)
                                        sandbox_tool_results.append(
                                            ToolMessage(content=error_msg, tool_call_id=call.get('id', 'unknown'))
                                        )
                                        await self._send_ws_message(
                                            socket, {'e': 'tool_error', 'tool': tool_name, 'message': error_msg}
                                        )

                                    await asyncio.sleep(0.02)
                                else:
                                    context_tool_calls.append(call)

                            if sandbox_tool_results:
                                current_state['messages'] = list(current_state['messages']) + sandbox_tool_results

                                if not context_tool_calls:
                                    continue_state = {
                                        'messages': current_state['messages'],
                                        'iteration_count': current_state.get('iteration_count', 0),
                                    }

                elif 'execute_tools' in chunk:
                    tools_node_output = chunk['execute_tools']
                    new_messages = tools_node_output.get('messages', [])

                    if new_messages:
                        current_state['messages'] = list(current_state['messages']) + new_messages
                        current_state['iteration_count'] = tools_node_output.get(
                            'iteration_count', current_state.get('iteration_count', 0)
                        )

                    logger.debug('Graph executed tools node')

            try:
                host = sandbox.get_host(5173)
                url = f'https://{host}'
                print(f'🌐 Project live at: {url}')

            except Exception as e:
                logger.warning(f'Could not get sandbox host: {e}')

        except Exception as e:
            error_msg = f'❌ Error in agent stream: {e}'
            logger.error(error_msg, exc_info=True)
            await self._send_ws_message(socket, {'e': 'error', 'message': str(e)})
            raise


agent_service = AgentService()
