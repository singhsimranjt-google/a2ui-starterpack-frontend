import { AuthConfig } from '../types';

export function toEnv(auth: AuthConfig): Record<string, string> {
  if (auth.mode === 'api-key') {
    return {
      GOOGLE_GENAI_USE_VERTEXAI: 'false',
      GEMINI_API_KEY: auth.geminiApiKey,
      GOOGLE_API_KEY: auth.geminiApiKey,
    };
  }
  return {
    GOOGLE_GENAI_USE_VERTEXAI: 'true',
    GOOGLE_CLOUD_PROJECT: auth.gcpProject,
    GOOGLE_CLOUD_LOCATION: auth.gcpLocation,
  };
}
