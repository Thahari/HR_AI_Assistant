import json

def load_roles():
    with open("config/roles.json", "r") as f:
        return json.load(f)

def get_role_skills(role_name):
    roles = load_roles()
    return roles.get(role_name, [])