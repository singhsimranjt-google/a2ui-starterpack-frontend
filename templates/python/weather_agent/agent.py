"""Google ADK & A2UI Weather Agent definition."""

import os
from google.adk.agents import llm_agent
from google.genai import types

from a2ui.schema import common_modifiers
from a2ui.schema import constants as a2ui_constants
from a2ui.schema import manager as a2ui_schema_manager
from a2ui.basic_catalog.provider import BasicCatalog

from . import a2ui_utils
from .config import config
from .prompt import ROLE_DESCRIPTION, UI_DESCRIPTION
from .tools import get_current_weather

_EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples/v0_9")
_CATALOG_CONFIG = BasicCatalog.get_config(
    version=a2ui_constants.VERSION_0_9,
    examples_path=_EXAMPLES_DIR,
)

_SCHEMA_MANAGER = a2ui_schema_manager.A2uiSchemaManager(
    version=a2ui_constants.VERSION_0_9,
    catalogs=[_CATALOG_CONFIG],
    schema_modifiers=[common_modifiers.remove_strict_validation],
)

instruction = _SCHEMA_MANAGER.generate_system_prompt(
    role_description=ROLE_DESCRIPTION,
    ui_description=UI_DESCRIPTION,
    include_schema=True,
    include_examples=True,
    validate_examples=False,
).replace("${expression}", "${<expression>}")

# Google ADK Root Agent definition
root_agent = llm_agent.LlmAgent(
    name=config.agent_id,
    model=config.gemini_model,
    description=config.agent_description,
    instruction=instruction,
    tools=[get_current_weather],
    after_model_callback=a2ui_utils.a2ui_callback,
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=65536,
        temperature=0.2,
    ),
)
