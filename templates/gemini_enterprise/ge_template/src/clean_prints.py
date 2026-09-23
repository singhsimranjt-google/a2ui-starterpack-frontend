import os
import re

def comment_prints(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()
        
    for i in range(len(lines)):
        if "print(f\"\\n--- 🛠️ TOOL CALL:" in lines[i]:
            lines[i] = "    # " + lines[i].lstrip()
        elif "print(f\"Returns:" in lines[i]:
            lines[i] = "    # " + lines[i].lstrip()
        elif "print(f\"\\n🤖 [LLM RESPONSE]:" in lines[i]:
            lines[i] = "    # " + lines[i].lstrip()
        elif "print(f\"\\n✅ [TOOL FINISHED]:" in lines[i]:
            lines[i] = "        # " + lines[i].lstrip()
            
    with open(file_path, "w") as f:
        f.writelines(lines)
        
    print(f"Cleaned {file_path}")

base = "/usr/local/google/home/sidchaudhary/Desktop/A2UI/Gemini_enterprise/clinic_scheduling_agent/src"
comment_prints(os.path.join(base, "tools.py"))
comment_prints(os.path.join(base, "a2ui_utils.py"))

