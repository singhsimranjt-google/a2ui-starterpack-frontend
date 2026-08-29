import * as p from '@clack/prompts';
import pc from 'picocolors';
import path from 'path';
import { promptProjectConfig } from './prompts/project';
import { resolveGenerator } from './generators';
import { checkPrerequisites } from './utils/prerequisites';
import { printBanner } from './utils/banner';
import { ProjectConfig } from './types';

export async function runCli(overrideConfig?: Partial<ProjectConfig>): Promise<void> {
  printBanner();

  try {
    let config: ProjectConfig | null = null;

    if (overrideConfig && overrideConfig.projectType && overrideConfig.projectName) {
      const projectName = overrideConfig.projectName;
      config = {
        projectType: overrideConfig.projectType,
        frontendFramework: overrideConfig.frontendFramework,
        pythonRendererType: overrideConfig.pythonRendererType,
        projectName,
        targetDir: overrideConfig.targetDir || path.resolve(process.cwd(), projectName)
      };
    } else {
      config = await promptProjectConfig();
    }

    if (!config) {
      return;
    }

    const generator = resolveGenerator(config);

    // Prerequisite check
    const s = p.spinner();
    s.start(`Checking prerequisites for ${generator.name}...`);
    const prereqs = generator.getPrerequisites(config);
    const prereqsMet = checkPrerequisites(config, prereqs);
    s.stop(prereqsMet ? pc.green('Prerequisites verified') : pc.yellow('Prerequisite warnings noted'));

    // Generation
    s.start(`Scaffolding ${pc.cyan(config.projectName)} using ${generator.name}...`);
    const result = await generator.generate(config.targetDir, config);

    if (!result.success) {
      s.stop(pc.red('Generation failed'));
      p.note(
        result.error?.message || 'An unknown error occurred during generation.',
        pc.red('Error Details')
      );
      process.exit(1);
    }

    s.stop(pc.green(`Created ${result.generatedFiles.length} files successfully!`));

    // Display summary and next steps
    p.note(
      result.nextSteps.map((step) => pc.cyan(step)).join('\n'),
      pc.bold(pc.green('Next Steps'))
    );

    p.outro(pc.green(`✨ Successfully scaffolded ${pc.bold(config.projectName)}! Happy building with Google ADK & A2UI!`));

  } catch (err: any) {
    p.cancel(pc.red(`Fatal error: ${err.message}`));
    process.exit(1);
  }
}
