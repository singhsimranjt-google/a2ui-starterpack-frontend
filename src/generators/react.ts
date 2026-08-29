import { BaseGenerator } from './base';
import { ProjectConfig, PrerequisiteRequirement } from '../types';
import { COMMON_PREREQUISITES } from '../utils/prerequisites';

export class ReactGenerator extends BaseGenerator {
  readonly id = 'react';
  readonly name = 'React + Vite (TypeScript)';
  readonly description = 'React 18/19 + Vite frontend application with interactive A2UI streaming renderer';
  protected readonly templateSubdir = 'react';

  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[] {
    return [
      COMMON_PREREQUISITES.node,
      COMMON_PREREQUISITES.npm
    ];
  }

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    return [
      `cd ${config.projectName}`,
      'npm install',
      'npm run dev',
      'Open http://localhost:5173 in your browser'
    ];
  }
}
