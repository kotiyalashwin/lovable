from langchain_core.tools import tool
from pathlib import Path
import json
from typing import Optional


@tool
async def create_file(file_path: str, content: str) -> str:
    """
    Create a file with the given content at the specified path.
    
    Args:
        file_path: The path where the file should be created (e.g., "src/App.jsx")
        content: The content to write to the file
    
    Returns:
        Success message indicating the file was created
    """
    # Tool interface - actual execution handled in agent_service
    # This allows the LLM to understand the tool signature
    return f"File {file_path} will be created with {len(content)} characters"


@tool
async def read_file(file_path: str) -> str:
    """
    Read the content of a file from the project.
    
    Args:
        file_path: The path of the file to read (relative to project root)
    
    Returns:
        The content of the file, or an error message if file doesn't exist
    """
    # Tool interface - actual execution handled in agent_service
    return f"Reading file {file_path}"


@tool
async def execute_command(command: str) -> str:
    """
    Execute a shell command in the project environment.
    
    Args:
        command: The command to execute (e.g., "npm install", "npm run dev")
    
    Returns:
        Command output including stdout, stderr, and exit code
    """
    # Tool interface - actual execution handled in agent_service
    return f"Executing command: {command}"


@tool
async def save_context(semantic: str, procedural: str = "", episodic: str = "") -> str:
    """
    Save project context including semantic, procedural, and episodic memory
    inside a context/ folder for future sessions.

    Args:
        semantic: Natural-language summary of the current project state (components, pages, libs).
        procedural: Instructions or conventions on how to modify or extend the project.
        episodic: Recent reasoning or decisions made by the agent.

    Returns:
        A success message with path to the saved file.
    """
    # Tool interface - actual execution handled in agent_service
    return "Context will be saved for future sessions"


@tool
async def get_context() -> str:
    """
    Fetch the last saved context for a project. This retrieves semantic, procedural,
    and episodic memory along with the code map from previous sessions.

    Returns:
        The previous context data including semantic, procedural, episodic memory, and code_map,
        or a message indicating no context exists for a fresh project.
    """
    # Tool interface - actual execution handled in agent_service
    return "Retrieving context from previous sessions"
