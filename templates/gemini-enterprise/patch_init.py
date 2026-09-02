import re

agent_path = 'src/agent.py'
with open(agent_path, 'r') as f:
    code = f.read()

new_init = '''    def __init__(self):
        self.config = config
        self.client: Optional[Any] = None
        if GENAI_AVAILABLE:
            if config.use_vertexai and config.gcp_project:
                # Use Vertex AI via Application Default Credentials (ADC) for Argolis
                self.client = Client(vertexai=True, project=config.gcp_project, location=config.gcp_region)
            elif config.api_key:
                self.client = Client(api_key=config.api_key)
        self.system_instruction = f"{ROLE_DESCRIPTION}\\n\\n{UI_DESCRIPTION}"'''

code = re.sub(r'    def __init__\(self\):.*?self\.system_instruction = .*?\n', new_init + '\n', code, flags=re.DOTALL)

with open(agent_path, 'w') as f:
    f.write(code)
