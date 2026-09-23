import * as p from '@clack/prompts';
import spawn from 'cross-spawn';
import { AuthConfig } from '../types';
import { detectApiKey, detectGcloudProject, adcIsLive } from '../utils/auth-detect';

export async function promptAuth(): Promise<AuthConfig | null> {
  const mode = await p.select({
    message: 'How would you like to authenticate with Gemini?',
    options: [
      { value: 'api-key', label: 'Gemini API Key', hint: 'Simplest, for prototyping' },
      { value: 'vertex-adc', label: 'Google Cloud Vertex AI (Argolis/ADC)', hint: 'For enterprise use' },
    ],
  });

  if (p.isCancel(mode)) return null;

  if (mode === 'api-key') {
    const detectedKey = detectApiKey();
    const key = await p.password({
      message: 'Enter your Gemini API Key:',
      mask: '*',
      validate: (v) => {
        if (!v && !detectedKey) return 'API Key is required';
        return undefined;
      }
    });
    if (p.isCancel(key)) return null;
    return { mode: 'api-key', geminiApiKey: (key as string) || (detectedKey as string) };
  } else {
    const detected = detectGcloudProject();
    const project = await p.text({
      message: 'GCP / Argolis project ID:',
      initialValue: detected ?? '',
      placeholder: detected ?? 'my-argolis-project',
      validate: (v) => (!v?.trim() ? 'Project ID is required' : undefined)
    });
    if (p.isCancel(project)) return null;

    const location = await p.select({
      message: 'Vertex AI location:',
      initialValue: 'us-central1',
      options: [
        { value: 'us-central1', label: 'us-central1' },
        { value: 'us-east4',    label: 'us-east4' },
        { value: 'europe-west4',label: 'europe-west4' },
      ]
    });
    if (p.isCancel(location)) return null;

    if (!adcIsLive()) {
      const go = await p.confirm({
        message: 'No Application Default Credentials found. Run `gcloud auth application-default login` now?',
        initialValue: true
      });
      if (p.isCancel(go) || !go) {
        p.log.warn('Skipping ADC login. Meta-agent might fail.');
      } else {
        p.log.step('Opening browser for ADC login...');
        spawn.sync('gcloud', ['auth', 'application-default', 'login'], { stdio: 'inherit' });
        spawn.sync('gcloud', ['auth', 'application-default', 'set-quota-project', project as string], { stdio: 'inherit' });
      }
    }

    return { mode: 'vertex-adc', gcpProject: project as string, gcpLocation: location as string };
  }
}
