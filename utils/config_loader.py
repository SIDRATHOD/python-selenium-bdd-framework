import json
import os

def load_config():
    
    file_path = os.path.join("config", f"config.json")
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Config file not found at {file_path}")

    with open(file_path, "r") as f:
        config = json.load(f)

    # Resolve project root dynamically
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Handle local HTML base_url
    if config["base_url"].endswith(".html"):
        config["base_url"] = "file://" + os.path.join(project_root, config["base_url"])

    # Resolve test file paths
    config["small_image"] = os.path.join(project_root, config["small_image"])
    config["large_image"] = os.path.join(project_root, config["large_image"])

    return config
