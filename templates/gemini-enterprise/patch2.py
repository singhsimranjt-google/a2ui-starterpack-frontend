import re
with open('src/agent.py', 'r') as f:
    code = f.read()
code = re.sub(r'self\.system_instruction = f"\{ROLE_DESCRIPTION\}\n', 'self.system_instruction = f"{ROLE_DESCRIPTION}\\n\\n{UI_DESCRIPTION}"\n', code)
with open('src/agent.py', 'w') as f:
    f.write(code)
