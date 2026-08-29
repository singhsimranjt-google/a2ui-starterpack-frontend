import pc from 'picocolors';

export const logger = {
  info: (msg: string) => console.log(pc.cyan('ℹ ') + pc.white(msg)),
  success: (msg: string) => console.log(pc.green('✔ ') + pc.bold(pc.white(msg))),
  warn: (msg: string) => console.log(pc.yellow('⚠ ') + pc.yellow(msg)),
  error: (msg: string) => console.log(pc.red('✖ ') + pc.red(msg)),
  step: (step: string, detail?: string) => {
    console.log(pc.blue('◆ ') + pc.bold(step) + (detail ? pc.dim(` (${detail})`) : ''));
  },
  dim: (msg: string) => console.log(pc.dim(msg)),
  highlight: (msg: string) => pc.cyan(pc.bold(msg)),
  path: (p: string) => pc.magenta(p),
  code: (c: string) => pc.green(c)
};
