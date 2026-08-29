import path from 'path';
import fs from 'fs-extra';

export function validateProjectName(name: string): string | true {
  const trimmed = name.trim();
  if (!trimmed) {
    return 'Project name cannot be empty.';
  }

  // Enforce valid npm/folder naming
  const validPattern = /^[a-zA-Z0-9-_]+$/;
  if (!validPattern.test(trimmed)) {
    return 'Project name must contain only letters, numbers, hyphens (-) and underscores (_).';
  }

  return true;
}

export function sanitizeProjectName(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9-_]/g, '-');
}

export function formatProjectTitle(name: string): string {
  return name
    .split(/[-_]/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function isDirectoryEmpty(dirPath: string): boolean {
  if (!fs.existsSync(dirPath)) {
    return true;
  }
  const files = fs.readdirSync(dirPath);
  return files.length === 0;
}
