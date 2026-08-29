#!/usr/bin/env node

import { Command } from 'commander';
import { runCli } from './cli';
import { ProjectType, FrontendFramework, PythonRendererType } from './types';

const program = new Command();

program
  .name('goog-adk-a2ui-starter')
  .description('Official Scaffolding CLI for Google ADK and A2UI applications')
  .version('1.0.0')
  .argument('[project-name]', 'Target project directory name')
  .option('-t, --type <type>', 'Project type (frontend, python, fullstack)')
  .option('-f, --frontend <framework>', 'Frontend framework (angular, react)')
  .option('-r, --renderer <type>', 'Python renderer architecture (adk-a2ui, gemini-enterprise)')
  .action(async (projectName, options) => {
    let overrideConfig: any = undefined;

    if (options.type && projectName) {
      overrideConfig = {
        projectName,
        projectType: options.type as ProjectType,
        frontendFramework: options.frontend as FrontendFramework,
        pythonRendererType: (options.renderer as PythonRendererType) || (options.type === 'python' ? 'adk-a2ui' : undefined)
      };
    }

    await runCli(overrideConfig);
  });

program.parse(process.argv);
