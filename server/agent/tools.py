from langchain_core.tools import tool
from typing import Optional

@tool
async def create_file(file_path: str, content: str) -> dict:
    """
    Create a file with the given content at the specified path.
    
    Args:
        file_path: The path where the file should be created (e.g., "src/App.jsx")
        content: The content to write to the file
    
    Returns:
        A dictionary with file_path and success status
    """
    # This tool now just defines the interface
    # Actual execution happens in the agent service
    return {
        "file_path": file_path,
        "content": content,
        "action": "create_file"
    }


@tool
async def read_file(file_path: str) -> dict:
    """
    Read the content of a file.
    
    Args:
        file_path: The path of the file to read
    
    Returns:
        The content of the file
    """
    return {
        "file_path": file_path,
        "action": "read_file"
    }


@tool
async def execute_command(command: str) -> dict:
    """
    Execute a shell command in the project environment.
    
    Args:
        command: The command to execute (e.g., "npm install", "npm run dev")
    
    Returns:
        Command output and status
    """
    return {
        "command": command,
        "action": "execute_command"
    }   

@tool
async def save_context(semantic: str,procedural: str = "",episodic: str = "") -> dict:
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
    return {
        "action" : "save_context"
    } 
