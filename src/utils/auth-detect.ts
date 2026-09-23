import spawn from 'cross-spawn';

export const detectApiKey = (): string | undefined =>
  process.env.GEMINI_API_KEY || process.env.GOOGLE_API_KEY;

export const detectGcloudProject = (): string | undefined => {
  try {
    const r = spawn.sync('gcloud', ['config', 'get-value', 'project'], { encoding: 'utf-8' });
    const v = (r.stdout || '').trim();
    return v && v !== '(unset)' ? v : undefined;
  } catch { return undefined; }
};

export const adcIsLive = (): boolean => {
  try {
    return spawn.sync('gcloud', ['auth', 'application-default', 'print-access-token'],
             { stdio: 'ignore' }).status === 0;
  } catch { return false; }
};
