/**
 * Chat and agent runtime type definitions.
 */

export interface ChatMessage {
  sender: 'user' | 'agent';
  text: string;
  timestamp: string;
  surfaceId?: string;
}

export type AgentStatus = 'connected' | 'idle' | 'executing';
