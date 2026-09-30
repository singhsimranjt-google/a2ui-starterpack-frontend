import { Component, inject, signal, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { A2uiRendererService, SurfaceComponent } from '@a2ui/angular/v0_9';
import { A2uiMessage } from '@a2ui/web_core/v0_9';

import { ChatMessage, AgentStatus } from './models/chat.types';
import { MarkdownPipe } from './pipes/markdown.pipe';
import { ChatHeaderComponent } from './components/chat-header/chat-header.component';
import { ChatInputComponent } from './components/chat-input/chat-input.component';
import { AgentLoaderComponent } from './components/agent-loader/agent-loader.component';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    SurfaceComponent,
    MarkdownPipe,
    ChatHeaderComponent,
    ChatInputComponent,
    AgentLoaderComponent,
  ],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css'],
})
export class AppComponent implements OnInit {
  title = signal('Agent UI');
  agentStatus = signal<AgentStatus>('connected');
  messages = signal<ChatMessage[]>([]);

  private readonly rendererService = inject(A2uiRendererService);
  private readonly apiUrl = 'http://127.0.0.1:8080/api/agent/chat';
  private readonly infoUrl = 'http://127.0.0.1:8080/api/agent/info';
  private readonly sessionId = crypto.randomUUID();

  ngOnInit() {
    this.loadAgentInfo();
    this.sendInitialGreeting();
  }

  /**
   * Pull the agent's display name from the backend so this shell stays generic.
   * Deliberately NOT awaited in ngOnInit — the greeting must not wait on it.
   */
  private async loadAgentInfo() {
    try {
      const res = await fetch(this.infoUrl);
      if (!res.ok) return;              // older agent w/o the endpoint -> keep default
      const info = await res.json();
      if (info?.name) {
        this.title.set(info.name);
        document.title = info.name;     // browser tab
      }
    } catch {
      // Backend not up yet. Keep the placeholder rather than breaking the shell.
    }
  }


  /**
   * Request initial greeting from the backend agent.
   */
  private async sendInitialGreeting() {
    this.agentStatus.set('executing');
    try {
      const data = await this.postChat('Hello');
      const surfaceId = this.processA2uiPayload(data.a2ui);
      this.messages.set([
        {
          sender: 'agent',
          text: data.text || `Hello! 👋 I am your ${this.title()}.`,
          timestamp: new Date().toLocaleTimeString(),
          surfaceId,
        },
      ]);
      this.agentStatus.set('connected');
    } catch (err) {
      console.error('Failed to fetch initial greeting:', err);
      this.messages.set([
        {
          sender: 'agent',
          text: '⚠️ Could not connect to the agent at `http://127.0.0.1:8080/api/agent/chat`. Please start the backend service.',
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      this.agentStatus.set('idle');
    }
  }

  /**
   * Sends user message to backend agent and appends response.
   */
  async sendMessage(prompt: string) {
    const text = prompt.trim();
    if (!text) return;

    this.messages.update((prev) => [
      ...prev,
      {
        sender: 'user',
        text,
        timestamp: new Date().toLocaleTimeString(),
      },
    ]);

    this.agentStatus.set('executing');

    try {
      const data = await this.postChat(text);
      const surfaceId = this.processA2uiPayload(data.a2ui);

      this.messages.update((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: data.text || 'Response received from the agent.',
          timestamp: new Date().toLocaleTimeString(),
          surfaceId,
        },
      ]);
      this.agentStatus.set('connected');
    } catch (err) {
      console.error('Failed to communicate with agent backend:', err);
      this.messages.update((prev) => [
        ...prev,
        {
          sender: 'agent',
          text: `⚠️ Could not reach the agent at \`http://127.0.0.1:8080\`. Please ensure the backend is running.`,
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      this.agentStatus.set('idle');
    }
  }

  /**
   * HTTP POST helper for communicating with the FastAPI agent endpoint.
   */
  private async postChat(prompt: string): Promise<any> {
    const response = await fetch(this.apiUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, session_id: this.sessionId }),
    });
    if (!response.ok) {
      throw new Error(`Agent backend responded with status: ${response.status}`);
    }
    return response.json();
  }

  /**
   * Processes A2UI protocol messages through the A2UI renderer service and extracts the surfaceId.
   */
  private processA2uiPayload(a2ui?: any[]): string | undefined {
    if (!a2ui || !Array.isArray(a2ui) || a2ui.length === 0) {
      return undefined;
    }
    try {
      let surfaceId: string | undefined;
      for (const msg of a2ui) {
        if (msg.createSurface?.surfaceId) {
          surfaceId = msg.createSurface.surfaceId;
          break;
        }
        if (msg.updateComponents?.surfaceId) {
          surfaceId = msg.updateComponents.surfaceId;
          break;
        }
      }
      this.rendererService.processMessages(a2ui as A2uiMessage[]);
      return surfaceId;
    } catch (error) {
      console.error('A2UI message processing failed:', error);
      return undefined;
    }
  }

  @HostListener('window:a2ui-action', ['$event'])
  async onA2uiAction(event: any) {
    const action = event.detail;
    const promptText = String(action?.context?.prompt || '').trim() || `Submitted "${action?.name || 'action'}"`;
    this.agentStatus.set('executing');

    // Simulate user sending an "action" message
    this.messages.update((prev) => [
      ...prev,
      { sender: 'user', text: promptText, timestamp: new Date().toLocaleTimeString() }
    ]);

    try {
      const response = await fetch(this.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: promptText, action, session_id: this.sessionId })
      });
      const data = await response.json();
      const surfaceId = this.processA2uiPayload(data.a2ui);

      this.messages.update((prev) => [
        ...prev,
        { sender: 'agent', text: data.text || 'Action processed.', timestamp: new Date().toLocaleTimeString(), surfaceId }
      ]);
      this.agentStatus.set('connected');
    } catch (err) {
      console.error(err);
      this.agentStatus.set('idle');
    }
  }

}
