import path from 'path';
import { IGenerator, ProjectConfig, GenerationResult, PrerequisiteRequirement } from '../types';
import { getTemplateRoot, copyTemplateFiles, buildTemplateVariables } from '../utils/template';

export abstract class BaseGenerator implements IGenerator {
  abstract readonly id: string;
  abstract readonly name: string;
  abstract readonly description: string;
  protected abstract readonly templateSubdir: string;

  abstract getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[];
  abstract getNextSteps(targetDir: string, config: ProjectConfig): string[];

  async generate(targetDir: string, config: ProjectConfig): Promise<GenerationResult> {
    try {
      let generatedFiles: string[] = [];

      if (!config.useMetaAgent) {
        const templateDir = path.join(getTemplateRoot(), this.templateSubdir);
        generatedFiles = copyTemplateFiles(templateDir, targetDir, this.getVariables(config));
      }

      await this.postProcess(targetDir, config);

      return {
        success: true,
        targetDir,
        generatedFiles,
        nextSteps: this.getNextSteps(targetDir, config)
      };
    } catch (error: any) {
      return {
        success: false,
        targetDir,
        generatedFiles: [],
        nextSteps: [],
        error
      };
    }
  }

  protected getVariables(config: ProjectConfig): Record<string, string> {
    return buildTemplateVariables(config.projectName);
  }

  protected async postProcess(targetDir: string, config: ProjectConfig): Promise<void> {
    // Hook for generators that need post-processing (e.g. file tweaks)
  }
}
