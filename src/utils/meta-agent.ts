import * as p from '@clack/prompts';
import spawn from 'cross-spawn';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import pc from 'picocolors';
import { AuthConfig } from '../types';
import { toEnv } from './auth-env';
import { getTemplateRoot } from './template';

export interface MetaAgentResult {
  agentName: string;
  nested: boolean;
}

export async function runMetaAgent(options: {
  variant: 'adk-a2ui' | 'gemini-enterprise';
  authEnv: AuthConfig;
  targetDir: string;
}): Promise<MetaAgentResult | null> {
  const idea = await p.text({
    message: 'What kind of agent do you want to build?',
    placeholder: 'e.g. A clinic scheduling assistant that books doctor appointments',
    validate: (v) => (!v?.trim() ? 'Please describe your agent' : undefined)
  });
  if (p.isCancel(idea)) return null;

  // dist/templates/meta/<variant> - getTemplateRoot handles dev vs published
  const bundle = path.join(getTemplateRoot(), 'meta', options.variant);
  if (!fs.existsSync(bundle)) {
    p.log.error(pc.red(`Meta-agent bundle missing: ${bundle}`));
    p.log.info('Run `npm run build` to regenerate dist/templates.');
    return null;
  }

  const staging = await fs.mkdtemp(path.join(os.tmpdir(), 'a2ui-meta-'));

  try {
    await fs.copy(bundle, staging);
    const before = new Set(await fs.readdir(staging));

    p.log.step(pc.cyan('Launching the interactive meta-agent...'));
    p.log.info(pc.dim('You will now talk to the planner. Approve the flow to generate code.'));
    console.log();

    // stdio:'inherit' hands the TTY to Python so the ASCII planner loop works.
    const res = spawn.sync(
      'uv',
      ['run', '--with', 'google-genai', '--with', 'python-dotenv',
        'python', 'root_agent.py', idea as string],
      {
        cwd: staging,
        stdio: 'inherit',
        env: { ...process.env, ...toEnv(options.authEnv) }
      }
    );

    console.log();
    if (res.status !== 0) {
      p.log.error(pc.red('Meta-agent failed or was cancelled.'));
      return null;
    }

    // // Whatever new directory appeared is the generated agent.
    // const after = await fs.readdir(staging);
    // const produced = after.filter(
    //   (d) => !before.has(d) && fs.statSync(path.join(staging, d)).isDirectory()
    // );

    // `uv run` creates .venv/ inside the staging dir, so it shows up as a brand
    // new directory right next to the real output. Never mistake it for the agent.
    const IGNORED_OUTPUT = new Set([
      'venv', 'node_modules', '__pycache__',
      '.venv', '.uv', '.git', '.ruff_cache', '.pytest_cache', '.mypy_cache',
    ]);

    const after = await fs.readdir(staging);
    const produced = after.filter((d) => {
      if (before.has(d)) return false;
      if (d.startsWith('.')) return false;
      if (IGNORED_OUTPUT.has(d)) return false;
      return fs.statSync(path.join(staging, d)).isDirectory();
    });

    if (produced.length === 0) {
      p.log.error(pc.red('Meta-agent produced no output directory.'));
      return null;
    }
    if (produced.length > 1) {
      p.log.warn(pc.yellow(`Multiple outputs found; using "${produced[0]}".`));
    }

    const agentName = produced[0];
    const producedPath = path.join(staging, agentName);

    // ge_template ships its own pyproject.toml and keeps code under src/, so it
    // becomes the project root directly. basic_template does not: its modules sit
    // at the top level and use relative imports (`from .agent import root_agent`),
    // so it must stay a package directory with the manifest beside it.
    const selfContained = fs.existsSync(path.join(producedPath, 'pyproject.toml'));

    await fs.remove(options.targetDir);

    if (selfContained) {
      await fs.move(producedPath, options.targetDir, { overwrite: true });
    } else {
      await fs.ensureDir(options.targetDir);
      await fs.move(producedPath, path.join(options.targetDir, agentName), { overwrite: true });

      // The generated agent needs a dependency manifest. The staging copy already
      // carries `[tool.uv] package = false`, which is exactly right here too:
      // `uv sync` installs the deps without trying to build the project.
      const stagedManifest = path.join(staging, 'pyproject.toml');
      if (fs.existsSync(stagedManifest)) {
        await fs.copy(stagedManifest, path.join(options.targetDir, 'pyproject.toml'));
      }
    }

    const where = selfContained
      ? `${path.basename(options.targetDir)}/`
      : `${path.basename(options.targetDir)}/${agentName}/`;
    p.log.success(pc.green(`Agent generated into ${where}`));

    return { agentName, nested: !selfContained };
  } finally {
    await fs.remove(staging).catch(() => { /* best effort */ });
  }
}
