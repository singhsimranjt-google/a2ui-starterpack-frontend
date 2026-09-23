export type ProjectType = 'frontend' | 'python' | 'fullstack' | 'gemini-enterprise';

export type FrontendFramework = 'angular' | 'react';

export type PythonRendererType = 'adk-a2ui' | 'gemini-enterprise';

export interface EnvConfig {
  geminiApiKey?: string;
  useVertexAi?: boolean;
  gcpProject?: string;
  gcpLocation?: string;
}


export type AuthMode = 'api-key' | 'vertex-adc';

export type AuthConfig =
  | { mode: 'api-key';    geminiApiKey: string }
  | { mode: 'vertex-adc'; gcpProject: string; gcpLocation: string };

export interface ProjectConfig {
  projectName: string;
  projectType: ProjectType;
  targetDir: string;
  frontendFramework?: FrontendFramework;
  pythonRendererType?: PythonRendererType;
  useMetaAgent?: boolean;
  authConfig?: AuthConfig;
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
