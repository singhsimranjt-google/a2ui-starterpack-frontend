with open("src/agent.py", "r") as f:
    c = f.read()
import re
new_init = '''    def __init__(self):
        self.config = config
        self.client: Optional[Any] = None
        if GENAI_AVAILABLE:
            if config.use_vertexai and config.gcp_project:
                self.client = Client(vertexai=True, project=config.gcp_project, location=config.gcp_region)
            elif config.api_key:
                self.client = Client(api_key=config.api_key)
        self.system_instruction = f"{ROLE_DESCRIPTION}\\n\\n{UI_DESCRIPTION}"'''
c = re.sub(r'    def __init__\(self\):.*?self\.system_instruction = f"\{ROLE_DESCRIPTION\}\\n\\n\{UI_DESCRIPTION\}"', new_init, c, flags=re.DOTALL)
with open("src/agent.py", "w") as f:
    f.write(c)
