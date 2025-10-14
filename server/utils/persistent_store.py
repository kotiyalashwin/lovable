import os
import json
PROJECT_DIR = "data/project"



def get_store_path(project_id: str):
    project_path = os.path.join(PROJECT_DIR, f"{project_id}")
    os.makedirs(project_path, exist_ok=True)
    return os.path.join(project_path, "file_store.json")


def save_file_store(project_id: str, file_store: list):
    with open(get_store_path(project_id), "w") as f:
        json.dump(file_store, f, indent=2)


def load_file_store(project_id: str):
    path = get_store_path(project_id)
    # print(path)
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []
