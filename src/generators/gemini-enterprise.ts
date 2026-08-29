import { BaseGenerator } from './base';
import { ProjectConfig, PrerequisiteRequirement } from '../types';
import { COMMON_PREREQUISITES } from '../utils/prerequisites';

export class GeminiEnterpriseGenerator extends BaseGenerator {
  readonly id = 'gemini-enterprise';
  readonly name = 'Gemini Enterprise (GE) Python Code';
  readonly description = 'Python agent tailored for native Gemini Enterprise UI card rendering and tool execution';
  protected readonly templateSubdir = 'gemini-enterprise';

  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[] {
    return [
      COMMON_PREREQUISITES.python,
      COMMON_PREREQUISITES.uv
    ];
  }

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    return [
      `cd ${config.projectName}`,
      'cp .env.example .env  # Configure GEMINI_API_KEY and GCP Project credentials',
      'uv sync',
      'uv run python src/agent.py  # Test GE Agent and UI card renderer',
      'uv run pytest  # Run test suite'
    ];
  }
}
