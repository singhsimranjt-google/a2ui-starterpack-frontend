import { BaseGenerator } from './base';
import { ProjectConfig, PrerequisiteRequirement } from '../types';
import { COMMON_PREREQUISITES } from '../utils/prerequisites';

export class AngularGenerator extends BaseGenerator {
  readonly id = 'angular';
  readonly name = 'Angular Frontend (A2UI)';
  readonly description = 'Standalone Angular client application for dynamic A2UI component rendering';
  protected readonly templateSubdir = 'angular';

  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[] {
    return [
      COMMON_PREREQUISITES.node,
      COMMON_PREREQUISITES.npm
    ];
  }

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    return [
      `cd ${config.projectName}`,
      'npm install --legacy-peer-deps',
      'npm start',
      'Open http://localhost:4200 in your browser'
    ];
  }
}
