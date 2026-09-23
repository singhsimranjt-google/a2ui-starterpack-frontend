import * as p from '@clack/prompts';
import spawn from 'cross-spawn';
import fs from 'fs-extra';
import path from 'path';
import os from 'os';
import pc from 'picocolors';
import { AuthConfig } from '../types';
import { toEnv } from './auth-env';
import { getTemplateRoot } from './template';

export async function runMetaAgent(options: {
  variant: 'adk-a2ui' | 'gemini-enterprise';
  authEnv: AuthConfig;
  targetDir: string;
}): Promise<boolean> {
  const idea = await p.text({
    message: 'What kind of agent do you want to build?',
    placeholder: 'e.g. A clinic scheduling assistant that books doctor appointments',
    validate: (v) => (!v?.trim() ? 'Please describe your agent' : undefined)
  });
  if (p.isCancel(idea)) return false;

  // dist/templates/meta/<variant> - getTemplateRoot handles dev vs published
  const bundle = path.join(getTemplateRoot(), 'meta', options.variant);
  if (!fs.existsSync(bundle)) {
    p.log.error(pc.red(`Meta-agent bundle missing: ${bundle}`));
    p.log.info('Run `npm run build` to regenerate dist/templates.');
    return false;
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
      return false;
    }

    // Whatever new directory appeared is the generated agent.
    const after = await fs.readdir(staging);
    const produced = after.filter(
      (d) => !before.has(d) && fs.statSync(path.join(staging, d)).isDirectory()
    );

    if (produced.length === 0) {
      p.log.error(pc.red('Meta-agent produced no output directory.'));
      return false;
    }
    if (produced.length > 1) {
      p.log.warn(pc.yellow(`Multiple outputs found; using "${produced[0]}".`));
    }

    // Only the generated agent reaches the user.
    // root_agent.py and the golden template stay behind in staging.
    await fs.remove(options.targetDir);
    await fs.move(path.join(staging, produced[0]), options.targetDir, { overwrite: true });

    p.log.success(pc.green(`Agent generated into ${path.basename(options.targetDir)}/`));
    return true;
  } finally {
    await fs.remove(staging).catch(() => { /* best effort */ });
  }
}
