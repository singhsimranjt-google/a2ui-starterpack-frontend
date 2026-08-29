import { BaseGenerator } from './base';
import { ProjectConfig, PrerequisiteRequirement } from '../types';
import { COMMON_PREREQUISITES } from '../utils/prerequisites';

export class PythonGenerator extends BaseGenerator {
  readonly id = 'python-adk';
  readonly name = 'Google ADK + A2UI Python Agent';
  readonly description = 'Python agent service with Google ADK, A2UI Schema Generation, and FastAPI server';
  protected readonly templateSubdir = 'python';

  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[] {
    return [
      COMMON_PREREQUISITES.python,
      COMMON_PREREQUISITES.uv
    ];
  }

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    return [
      `cd ${config.projectName}`,
      'cp .env.example .env  # Insert your GEMINI_API_KEY',
      'uv sync',
      'uv run python src/agent.py  # Test agent in CLI',
      'uv run uvicorn src.server:app --reload --port 8000  # Start API server'
    ];
  }
}
