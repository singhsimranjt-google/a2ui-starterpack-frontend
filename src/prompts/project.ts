import * as p from '@clack/prompts';
import path from 'path';
import pc from 'picocolors';
import { ProjectConfig, ProjectType, FrontendFramework, PythonRendererType, AuthConfig } from '../types';
import { validateProjectName, sanitizeProjectName, isDirectoryEmpty } from '../utils/validation';
import { promptAuth } from './auth';

export async function promptProjectConfig(): Promise<ProjectConfig | null> {
  p.intro(pc.bgCyan(pc.black(' goog-adk-a2ui-starter ')));

  
  // 1. What do you want to create?
  const projectType = await p.select<ProjectType>({
    message: 'What do you want to create?',
    options: [
      { value: 'frontend', label: 'Frontend', hint: 'Angular or React + Vite dynamic A2UI client' },
      { value: 'python', label: 'Python Agent', hint: 'Google ADK + A2UI' },
      { value: 'fullstack', label: 'Full stack', hint: 'Frontend Client + Google ADK Python Backend' },
      { value: 'gemini-enterprise', label: 'Gemini Enterprise', hint: 'Python agent for Gemini Enterprise UI' }
    ]
  });

  if (p.isCancel(projectType)) {
    p.cancel('Scaffolding cancelled.');
    return null;
  }

  let frontendFramework: FrontendFramework | undefined;
  let pythonRendererType: PythonRendererType | undefined;
  let authConfig: AuthConfig | undefined;
  let useMetaAgent = false;

  if (projectType === 'frontend') {
    const feChoice = await p.select<FrontendFramework>({
      message: 'Which frontend?',
      options: [
        { value: 'angular', label: 'Angular' },
        { value: 'react', label: 'React' }
      ]
    });
    if (p.isCancel(feChoice)) return null;
    frontendFramework = feChoice;
  }

  if (projectType === 'python') {
    pythonRendererType = 'adk-a2ui';
    const auth = await promptAuth();
    if (!auth) return null;
    authConfig = auth;
    useMetaAgent = true;
  }

  if (projectType === 'fullstack') {
    const feChoice = await p.select<FrontendFramework>({
      message: 'Which frontend framework for full-stack?',
      options: [
        { value: 'angular', label: 'Angular' },
        { value: 'react', label: 'React' }
      ]
    });
    if (p.isCancel(feChoice)) return null;
    frontendFramework = feChoice;
    pythonRendererType = 'adk-a2ui';
    const auth = await promptAuth();
    if (!auth) return null;
    authConfig = auth;
    useMetaAgent = true;
  }

  if (projectType === 'gemini-enterprise') {
    pythonRendererType = 'gemini-enterprise';
    const auth = await promptAuth();
    if (!auth) return null;
    authConfig = auth;
    useMetaAgent = true;
  }

  // 5. Project Name
  const defaultName = 'my-adk-app';
  const projectNameInput = await p.text({
    message: 'Project name:',
    placeholder: defaultName,
    defaultValue: defaultName,
    validate: (val) => {
      const check = validateProjectName(val || defaultName);
      if (typeof check === 'string') return check;
      return undefined;
    }
  });

  if (p.isCancel(projectNameInput)) {
    p.cancel('Scaffolding cancelled.');
    return null;
  }

  const projectName = sanitizeProjectName((projectNameInput as string) || defaultName);
  const targetDir = path.resolve(process.cwd(), projectName);

  // Check if directory already exists
  if (!isDirectoryEmpty(targetDir)) {
    const shouldOverwrite = await p.confirm({
      message: `Directory "${projectName}" is not empty. Continue anyway?`,
      initialValue: false
    });

    if (p.isCancel(shouldOverwrite) || !shouldOverwrite) {
      p.cancel('Scaffolding aborted to protect existing directory.');
      return null;
    }
  }

  
  return {
    projectType,
    frontendFramework,
    pythonRendererType,
    projectName,
    targetDir,
    useMetaAgent,
    authConfig
  };

}
