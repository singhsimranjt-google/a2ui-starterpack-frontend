# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Google ADK & A2UI Clinic Scheduling Agent definition."""

import os
from google.adk.agents import llm_agent
from google.genai import types

from a2ui.schema import common_modifiers
from a2ui.schema import constants as a2ui_constants
from a2ui.schema import manager as a2ui_schema_manager
# from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.catalog import CatalogConfig

from . import a2ui_utils
from .config import config
from .prompt import ROLE_DESCRIPTION, UI_DESCRIPTION
from . import tools

from google.adk.apps.app import App, EventsCompactionConfig

_EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples/v0_9")
# _CATALOG_CONFIG = BasicCatalog.get_config(
#     version=a2ui_constants.VERSION_0_9,
#     examples_path=_EXAMPLES_DIR,
# )
# Google publishes no machine-readable Material catalog schema (the spec URL
# 404s), so we load the reconstruction produced by gen_material_catalog.py.
_CATALOG_PATH = os.path.join(
    os.path.dirname(__file__), "catalogs", "material_catalog.json"
)
_CATALOG_CONFIG = CatalogConfig.from_path(
    name="material",
    catalog_path=_CATALOG_PATH,
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
    validate_examples=True,
).replace("${expression}", "${<expression>}")

# Google ADK Root Agent definition
root_agent = llm_agent.LlmAgent(
    name=config.agent_id,
    model=config.gemini_model,
    description=config.agent_description,
    instruction=instruction,
    tools=[
        tools.get_doctors_for_department,
        tools.check_doctor_availability,
        tools.confirm_appointment,
        tools.get_appointment_history,
        tools.reset_to_departments,
        tools.restart_flow,
    ],
    after_model_callback=a2ui_utils.a2ui_callback,
    before_model_callback=a2ui_utils.a2ui_before_model_callback,
    after_tool_callback=a2ui_utils.a2ui_after_tool_callback,
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=65536,
        temperature=0.2,
    ),
)

# Wrap the agent in an App with compaction
app = App(
    name=config.agent_id,
    root_agent=root_agent,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,   # compact every 3 user turns
        overlap_size=1,          # keep 1 turn of overlap for context
        token_threshold=30000,   # also compact if prompt exceeds 16k tokens
        event_retention_size=6,  # keep last 6 raw events un-compacted
    ),
)

