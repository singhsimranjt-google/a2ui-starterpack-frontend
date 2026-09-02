import re

agent_path = 'src/agent.py'
with open(agent_path, 'r') as f:
    code = f.read()

code = re.sub(r'\{"explicitList": (\[.*?\])\}', r'\1', code)

with open(agent_path, 'w') as f:
    f.write(code)
