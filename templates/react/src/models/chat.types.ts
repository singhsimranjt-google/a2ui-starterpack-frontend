
export type AgentStatus = 'idle' | 'executing' | 'connected' | 'error';

export interface ChatMessage {
  sender: 'user' | 'agent';
  text?: string;
  timestamp: string;
  surfaceId?: string;
}
