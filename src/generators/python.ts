import path from 'path';
import fs from 'fs-extra';
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

  protected async postProcess(targetDir: string, config: ProjectConfig): Promise<void> {
    const envConfig = config.envConfig;
    const apiKey = envConfig?.geminiApiKey || 'your-gemini-api-key-here';
    const gcpProject = envConfig?.gcpProject || 'your-gcp-project-id';
    const gcpLocation = envConfig?.gcpLocation || 'us-central1';
    const useVertex = envConfig?.useVertexAi ? 'TRUE' : 'FALSE';

    const envContent = [
      '# Google GenAI / Gemini API Keys',
      `GEMINI_API_KEY=${apiKey}`,
      '',
      '# Optional: Google Cloud Vertex AI configuration',
      `GOOGLE_GENAI_USE_VERTEXAI=${useVertex}`,
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
      'uv run uvicorn weather_agent.server:app --reload --port 8000  # Start API server'
    ];
  }
}
