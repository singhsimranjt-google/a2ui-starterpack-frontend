export type ProjectType = 'frontend' | 'python' | 'fullstack';

export type FrontendFramework = 'angular' | 'react';

export type PythonRendererType = 'adk-a2ui' | 'gemini-enterprise';

export interface EnvConfig {
  geminiApiKey?: string;
  useVertexAi?: boolean;
  gcpProject?: string;
  gcpLocation?: string;
}

export interface ProjectConfig {
  projectType: ProjectType;
  frontendFramework?: FrontendFramework;
  pythonRendererType?: PythonRendererType;
  projectName: string;
  targetDir: string;
  envConfig?: EnvConfig;
}

export interface PrerequisiteRequirement {
  name: string;
  command: string;
  args?: string[];
  required: boolean;
  installGuide: string;
}

export interface GenerationResult {
  success: boolean;
  targetDir: string;
  generatedFiles: string[];
  nextSteps: string[];
  error?: Error;
}

export interface IGenerator {
  readonly id: string;
  readonly name: string;
  readonly description: string;
  generate(targetDir: string, config: ProjectConfig): Promise<GenerationResult>;
  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[];
  getNextSteps(targetDir: string, config: ProjectConfig): string[];
}
