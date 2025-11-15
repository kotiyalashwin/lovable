from fastapi import FastAPI,WebSocket,WebSocketDisconnect 
from fastapi.middleware.cors  import CORSMiddleware
from fastapi.responses import JSONResponse 
import asyncio
from agent.agent_service import agent_service
from inject import inject
import json
app = FastAPI()
app.add_middleware(CORSMiddleware,allow_origins=["*"],allow_methods=["*"],allow_headers=["*"])

active_sockets={}
active_runs={}

@app.post("/chat/{project_id}")
async def create_project(project_id:str,payload:dict):
    prompt = payload.get("prompt")
    if not prompt:
        return JSONResponse({"error":"Too short or no description" }, status_code=400)
    
    if project_id in  active_runs:
        return JSONResponse({"error": "Project is being created.Kindly wait"}, status_code=409)
 
    async def task():
        try:
            socket = active_sockets[project_id]
            await agent_service.run_agent_stream(prompt, project_id, socket)
            
        except Exception as e:
            print(f"❌ Error in task: {e}")
            ws = active_sockets.get(project_id)
            if ws:
                try:
                    await ws.send_json({
                        "e": "error",
                        "message": str(e)
                    })
                except:
                    pass
        finally:
            active_runs.pop(project_id, None)
    
    active_runs[project_id] = asyncio.create_task(task())
    await active_runs[project_id]
    
    sandbox = agent_service.sandboxes.get(project_id)
    if sandbox is None :
        return {
            "status": "success",
            "project_id": project_id,
            "file_count": 0,
            "files": [],
            "sandbox_id": sandbox.sandbox_id if sandbox else None,
            "sandbox_active": project_id in agent_service.sandboxes
        } 
    result = await sandbox.commands.run(inject)
    files = json.loads(result.stdout)
    
    return {
        "status": "success",
        "project_id": project_id,
        "file_count": len(files),
        "files": files,
        "sandbox_id": sandbox.sandbox_id if sandbox else None,
        "sandbox_active": project_id in agent_service.sandboxes
}

@app.websocket("/ws/{project_id}")
async def ws_listener(websocket: WebSocket, project_id: str):
    await websocket.accept()
    active_sockets[project_id] = websocket

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print(f"WebSocket disconnected for project {project_id}")
    finally:
        active_sockets.pop(project_id, None)
        try:
            await agent_service.close_sandbox(project_id)
        except Exception as e:
            print(f"Error closing sandbox for project {project_id}: {e}")

