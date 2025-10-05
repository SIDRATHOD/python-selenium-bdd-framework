import json
import os
import yaml

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

def load_healing_config():
    """Loads the self-healing configuration from framework_config.yaml."""
    file_path = "framework_config.yaml"
    if not os.path.exists(file_path):
        # Return a default disabled config if file doesn't exist
        return {"self_healing": {"enabled": False}}

    with open(file_path, "r") as f:
        config = yaml.safe_load(f)

    return config