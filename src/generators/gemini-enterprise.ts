import path from 'path';
import fs from 'fs-extra';
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

  protected async postProcess(targetDir: string, config: ProjectConfig): Promise<void> {
    const envConfig = config.envConfig;
    const apiKey = envConfig?.geminiApiKey || 'your-gemini-api-key-here';
    const gcpProject = envConfig?.gcpProject || 'your-gcp-project-id';
    const gcpLocation = envConfig?.gcpLocation || 'us-central1';

    const envContent = [
      '# Google GenAI / Gemini Enterprise configuration',
      `GEMINI_API_KEY=${apiKey}`,
      `GOOGLE_CLOUD_PROJECT=${gcpProject}`,
      `GOOGLE_CLOUD_LOCATION=${gcpLocation}`,
      ''
    ].join('\n');

    fs.writeFileSync(path.join(targetDir, '.env'), envContent, 'utf-8');
    fs.writeFileSync(path.join(targetDir, '.env.example'), envContent, 'utf-8');
  }

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    return [
      `cd ${config.projectName}`,
      'uv sync',
      'uv run python src/agent.py  # Test GE Agent and UI card renderer',
      'uv run pytest  # Run test suite'
    ];
  }
}
