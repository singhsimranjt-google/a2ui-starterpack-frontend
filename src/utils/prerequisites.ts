import spawn from 'cross-spawn';
import { PrerequisiteRequirement, ProjectConfig } from '../types';
import { logger } from './logger';

export function checkBinaryExists(command: string, args: string[] = ['--version']): boolean {
  try {
    const result = spawn.sync(command, args, { stdio: 'ignore' });
    return result.status === 0;
  } catch {
    return false;
  }
}

export function checkPrerequisites(config: ProjectConfig, requirements: PrerequisiteRequirement[]): boolean {
  let allMet = true;

  for (const req of requirements) {
    const exists = checkBinaryExists(req.command, req.args);
    if (!exists) {
      if (req.required) {
        logger.error(`Missing required dependency: ${req.name} (${req.command})`);
        logger.info(`Installation instruction: ${req.installGuide}`);
        allMet = false;
      } else {
        logger.warn(`Optional dependency not detected: ${req.name} (${req.command})`);
        logger.dim(`Tip: ${req.installGuide}`);
      }
    }
  }

  return allMet;
}

export const COMMON_PREREQUISITES: Record<string, PrerequisiteRequirement> = {
  node: {
    name: 'Node.js',
    command: 'node',
    args: ['-v'],
    required: true,
    installGuide: 'Download Node.js from https://nodejs.org/'
  },
  npm: {
    name: 'npm',
    command: 'npm',
    args: ['-v'],
    required: true,
    installGuide: 'npm is packaged with Node.js.'
  },
  python: {
    name: 'Python 3',
    command: 'python3',
    args: ['--version'],
    required: true,
    installGuide: 'Install Python 3.10+ from https://www.python.org/ or your system package manager.'
  },
  uv: {
    name: 'uv (Fast Python Package Manager)',
    command: 'uv',
    args: ['--version'],
    required: true,
    installGuide: 'Install uv via `curl -LsSf https://astral.sh/uv/install.sh | sh` or `brew install uv`'
  }
};
