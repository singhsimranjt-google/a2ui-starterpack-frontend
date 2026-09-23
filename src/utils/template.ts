import fs from 'fs-extra';
import path from 'path';
import { formatProjectTitle } from './validation';

export function getTemplateRoot(): string {
  // Compiled: dist/utils/template.js -> dist/templates
  const bundled = path.resolve(__dirname, '../templates');
  if (fs.existsSync(bundled)) return bundled;

  // tsx/ts-node dev: src/utils/template.ts -> <pkg>/dist/templates
  const devBundled = path.resolve(__dirname, '../../dist/templates');
  if (fs.existsSync(devBundled)) return devBundled;

  // NOTE: never fall back to <pkg>/templates. That is the *source* tree
  // (frontend/, backend/, gemini_enterprise/) and has a different layout
  // from the bundled output. Run `npm run build` instead.
  return bundled;
}

export function copyTemplateFiles(
  templateSourceDir: string,
  targetDestinationDir: string,
  variables: Record<string, string>
): string[] {
  if (!fs.existsSync(templateSourceDir)) {
    throw new Error(`Template directory not found: ${templateSourceDir}`);
  }

  fs.ensureDirSync(targetDestinationDir);
  const createdFiles: string[] = [];

  const processDirectory = (srcDir: string, destDir: string) => {
    const entries = fs.readdirSync(srcDir, { withFileTypes: true });

    for (const entry of entries) {
      const srcPath = path.join(srcDir, entry.name);
      const destPath = path.join(destDir, entry.name);

      const ignoreList = ['node_modules', 'dist', '.angular', '.vite', '__pycache__', '.venv', '.env'];
      if (ignoreList.includes(entry.name)) {
        continue;
      }

      if (entry.isDirectory()) {
        fs.ensureDirSync(destPath);
        processDirectory(srcPath, destPath);
      } else if (entry.isFile()) {
        const isBinary = isBinaryFile(srcPath);
        if (isBinary) {
          fs.copyFileSync(srcPath, destPath);
        } else {
          let content = fs.readFileSync(srcPath, 'utf8');
          for (const [key, value] of Object.entries(variables)) {
            const pattern = new RegExp(`{{${key}}}`, 'g');
            content = content.replace(pattern, value);
          }
          fs.writeFileSync(destPath, content, 'utf8');
        }
        createdFiles.push(destPath);
      }
    }
  };

  processDirectory(templateSourceDir, targetDestinationDir);
  return createdFiles;
}

function isBinaryFile(filePath: string): boolean {
  const binaryExtensions = ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.pdf', '.zip', '.tar', '.gz', '.woff', '.woff2', '.ttf'];
  const ext = path.extname(filePath).toLowerCase();
  return binaryExtensions.includes(ext);
}

export function buildTemplateVariables(projectName: string, extras?: Record<string, string>): Record<string, string> {
  return {
    PROJECT_NAME: projectName,
    PROJECT_TITLE: formatProjectTitle(projectName),
    ...extras
  };
}
