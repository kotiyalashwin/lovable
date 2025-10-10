import os
import json
PROJECT_DIR = "project_session"
os.makedirs(PROJECT_DIR, exist_ok=True)



def get_store_path(project_id: str):
    return os.path.join(PROJECT_DIR, f"{project_id}_store.json")


def save_file_store(project_id: str, file_store: list):
    with open(get_store_path(project_id), "w") as f:
        json.dump(file_store, f, indent=2)


def load_file_store(project_id: str):
    path = get_store_path(project_id)
    print(path)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []
