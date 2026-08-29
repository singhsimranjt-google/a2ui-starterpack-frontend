import * as p from '@clack/prompts';
import path from 'path';
import pc from 'picocolors';
import { ProjectConfig, ProjectType, FrontendFramework, PythonRendererType } from '../types';
import { validateProjectName, sanitizeProjectName, isDirectoryEmpty } from '../utils/validation';

export async function promptProjectConfig(): Promise<ProjectConfig | null> {
  p.intro(pc.bgCyan(pc.black(' goog-adk-a2ui-starter ')));

  // 1. What do you want to create?
  const projectType = await p.select<ProjectType>({
    message: 'What do you want to create?',
    options: [
      { value: 'frontend', label: 'Frontend', hint: 'Angular or React + Vite dynamic A2UI client' },
      { value: 'python', label: 'Python Agent', hint: 'Google ADK + A2UI or Gemini Enterprise' },
      { value: 'fullstack', label: 'Full stack', hint: 'Frontend Client + Google ADK Python Backend' }
    ]
  });

  if (p.isCancel(projectType)) {
    p.cancel('Scaffolding cancelled.');
    return null;
  }

  let frontendFramework: FrontendFramework | undefined;
  let pythonRendererType: PythonRendererType | undefined;

  // 2. Branch: Frontend
  if (projectType === 'frontend') {
    const feChoice = await p.select<FrontendFramework>({
      message: 'Which frontend?',
      options: [
        { value: 'angular', label: 'Angular', hint: 'Standalone component architecture' },
        { value: 'react', label: 'React', hint: 'React 18/19 + TypeScript + Vite' }
      ]
    });

    if (p.isCancel(feChoice)) {
      p.cancel('Scaffolding cancelled.');
      return null;
    }
    frontendFramework = feChoice;
  }

  // 3. Branch: Python
  if (projectType === 'python') {
    const pyChoice = await p.select<PythonRendererType>({
      message: 'Which agent / renderer architecture?',
      options: [
        { 
          value: 'adk-a2ui', 
          label: 'Google ADK + A2UI Agent', 
          hint: 'Standard reasoning agent + FastAPI A2UI stream' 
        },
        { 
          value: 'gemini-enterprise', 
          label: 'Gemini Enterprise (GE Renderer)', 
          hint: 'Generates Python code only for Gemini Enterprise' 
        }
      ]
    });

    if (p.isCancel(pyChoice)) {
      p.cancel('Scaffolding cancelled.');
      return null;
    }
    pythonRendererType = pyChoice;
  }

  // 4. Branch: Full Stack
  if (projectType === 'fullstack') {
    const feChoice = await p.select<FrontendFramework>({
      message: 'Which frontend framework for full-stack?',
      options: [
        { value: 'angular', label: 'Angular', hint: 'Angular client in frontend/' },
        { value: 'react', label: 'React', hint: 'React + Vite in frontend/' }
      ]
    });

    if (p.isCancel(feChoice)) {
      p.cancel('Scaffolding cancelled.');
      return null;
    }
    frontendFramework = feChoice;
    pythonRendererType = 'adk-a2ui';
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
    targetDir
  };
}
