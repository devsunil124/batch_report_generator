import os
import json

CONFIG_FILE = "config.json"

def load_config():
    """
    Load the application configuration from a JSON file.

    Returns
    -------
    str
        The saved folder path, or an empty string if the file doesn't exist or is invalid.
    """
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f).get("folder_path", "")
        except:
            pass
    return ""

def save_config(path):
    """
    Save the application configuration to a JSON file.

    Parameters
    ----------
    path : str
        The folder path to save.
    """
    with open(CONFIG_FILE, 'w') as f:
        json.dump({"folder_path": path}, f)

