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
"""Google ADK & A2UI Hotel Portfolio Manager Agent definition."""

import os
from google.adk.agents import llm_agent
from google.genai import types

from a2ui.schema import common_modifiers
from a2ui.schema import constants as a2ui_constants
from a2ui.schema import manager as a2ui_schema_manager

from . import a2ui_utils
from .config import config
from .prompt import ROLE_DESCRIPTION, UI_DESCRIPTION
from . import tools

_EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples/v0_9")
_CATALOG_CONFIG = a2ui_utils.get_catalog_config(examples_path=_EXAMPLES_DIR)

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
        tools.get_hotels,
        tools.get_hotel_dashboard,
        tools.get_revenue_by_city,
        tools.get_hotel_map,
        tools.get_room_rates,
        tools.save_room_rates,
        tools.submit_maintenance_request,
        tools.restart_flow,
    ],
    after_model_callback=a2ui_utils.a2ui_callback,
    generate_content_config=types.GenerateContentConfig(
        max_output_tokens=8192,
        temperature=0.2,
    ),
)