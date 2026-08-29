import fs from 'fs-extra';
import path from 'path';

export function ensureDirectory(dirPath: string): void {
  fs.ensureDirSync(dirPath);
}

export function writeJsonFile(filePath: string, data: any): void {
  fs.outputJsonSync(filePath, data, { spaces: 2 });
}

export function readJsonFile<T = any>(filePath: string): T {
  return fs.readJsonSync(filePath);
}

export function fileExists(filePath: string): boolean {
  return fs.existsSync(filePath);
}

export function listFilesRecursive(dir: string): string[] {
  let results: string[] = [];
  if (!fs.existsSync(dir)) return results;

  const list = fs.readdirSync(dir);
  for (const file of list) {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results = results.concat(listFilesRecursive(filePath));
    } else {
      results.push(filePath);
    }
  }
  return results;
}
