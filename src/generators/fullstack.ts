import path from 'path';
import fs from 'fs-extra';
import { IGenerator, ProjectConfig, GenerationResult, PrerequisiteRequirement } from '../types';
import { AngularGenerator } from './angular';
import { ReactGenerator } from './react';
import { PythonGenerator } from './python';
import { getTemplateRoot, copyTemplateFiles, buildTemplateVariables } from '../utils/template';

export class FullStackGenerator implements IGenerator {
  readonly id = 'fullstack';
  readonly name = 'Full Stack (Frontend + Google ADK Python Backend)';
  readonly description = 'Composable full-stack application with frontend client and Python agent backend';

  getPrerequisites(config: ProjectConfig): PrerequisiteRequirement[] {
    const feGen = config.frontendFramework === 'angular' ? new AngularGenerator() : new ReactGenerator();
    const beGen = new PythonGenerator();

    const prereqs = [...feGen.getPrerequisites(config), ...beGen.getPrerequisites(config)];
    // Deduplicate by command
    return prereqs.filter((v, i, a) => a.findIndex(t => t.command === v.command) === i);
  }

  async generate(targetDir: string, config: ProjectConfig): Promise<GenerationResult> {
    try {
      const generatedFiles: string[] = [];
      const frontendDir = path.join(targetDir, 'frontend');
      const backendDir = path.join(targetDir, 'backend');

      fs.ensureDirSync(targetDir);
      fs.ensureDirSync(frontendDir);
      fs.ensureDirSync(backendDir);

      // 1. Scaffold Frontend
      const feGenerator = config.frontendFramework === 'angular' ? new AngularGenerator() : new ReactGenerator();
      const feConfig: ProjectConfig = {
        ...config,
        projectName: `${config.projectName}-frontend`,
        targetDir: frontendDir
      };
      const feResult = await feGenerator.generate(frontendDir, feConfig);
      if (!feResult.success) throw feResult.error || new Error('Frontend generation failed');
      generatedFiles.push(...feResult.generatedFiles);

      // 2. Scaffold Backend
      const beGenerator = new PythonGenerator();
      const beConfig: ProjectConfig = {
        ...config,
        projectName: `${config.projectName}-backend`,
        targetDir: backendDir
      };
      const beResult = await beGenerator.generate(backendDir, beConfig);
      if (!beResult.success) throw beResult.error || new Error('Backend generation failed');
      generatedFiles.push(...beResult.generatedFiles);

      // 3. Scaffold Root Orchestrator files
      const templateRoot = getTemplateRoot();
      const rootTemplateDir = path.join(templateRoot, 'fullstack-root');
      if (fs.existsSync(rootTemplateDir)) {
        const rootVars = buildTemplateVariables(config.projectName, {
          FRONTEND_TYPE: config.frontendFramework === 'angular' ? 'Angular' : 'React'
        });
        const rootFiles = copyTemplateFiles(rootTemplateDir, targetDir, rootVars);
        generatedFiles.push(...rootFiles);
      }

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

  getNextSteps(targetDir: string, config: ProjectConfig): string[] {
    const isAngular = config.frontendFramework === 'angular';
    return [
      `cd ${config.projectName}`,
      '# Terminal 1: Start Backend Agent Server',
      'cd backend && cp .env.example .env && uv sync && uv run uvicorn src.server:app --reload --port 8000',
      '# Terminal 2: Start Frontend Client',
      `cd frontend && npm install && ${isAngular ? 'npm start' : 'npm run dev'}`,
      '# Or install everything from root: npm run install:all'
    ];
  }
}
