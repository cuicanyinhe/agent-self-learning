#提供统一的绝对路径

import os

def get_project_root() -> str:
    current_file = os.path.abspath(__file__)
    curren_dir = os.path.dirname(current_file)
    project_root = os.path.dirname(curren_dir)

    return project_root

def get_abs_path(relative_path: str) -> str:
    project_root = get_project_root()
    return os.path.join(project_root, relative_path)
