import { IGenerator, ProjectConfig } from '../types';
import { AngularGenerator } from './angular';
import { ReactGenerator } from './react';
import { PythonGenerator } from './python';
import { GeminiEnterpriseGenerator } from './gemini-enterprise';
import { FullStackGenerator } from './fullstack';

export function resolveGenerator(config: ProjectConfig): IGenerator {
  if (config.projectType === 'frontend') {
    if (config.frontendFramework === 'angular') {
      return new AngularGenerator();
    }
    return new ReactGenerator();
  }

  if (config.projectType === 'python') {
    if (config.pythonRendererType === 'gemini-enterprise') {
      return new GeminiEnterpriseGenerator();
    }
    return new PythonGenerator();
  }

  if (config.projectType === 'fullstack') {
    return new FullStackGenerator();
  }

  throw new Error(`Unsupported project type: ${config.projectType}`);
}

export * from './base';
export * from './angular';
export * from './react';
export * from './python';
export * from './gemini-enterprise';
export * from './fullstack';
