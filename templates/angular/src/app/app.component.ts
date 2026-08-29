import { Component, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface A2UIActionCard {
  id: string;
  type: 'stat_card' | 'action_prompt' | 'form' | 'table';
  title: string;
  content: string;
  timestamp: string;
  metadata?: Record<string, any>;
}

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = signal('{{PROJECT_TITLE}}');
  agentStatus = signal<'connected' | 'idle' | 'executing'>('connected');
  userInput = signal('');

  // Sample dynamic A2UI components emitted by Google ADK Agent
  cards = signal<A2UIActionCard[]>([
    {
      id: 'card-1',
      type: 'stat_card',
      title: 'Agent Status & Health',
      content: 'Google ADK Reasoning Engine is online and ready to render dynamic UI schemas.',
      timestamp: new Date().toLocaleTimeString(),
      metadata: { model: 'gemini-2.5-flash', latency: '124ms', confidence: 0.98 }
    },
    {
      id: 'card-2',
      type: 'action_prompt',
      title: 'Recommended Action',
      content: 'Analyze user intent and generate structured A2UI component schemas.',
      timestamp: new Date().toLocaleTimeString(),
      metadata: { actionRequired: 'Review query payload' }
    }
  ]);

  triggerAgentAction() {
    if (!this.userInput().trim()) return;

    this.agentStatus.set('executing');
    const newCard: A2UIActionCard = {
      id: `card-${Date.now()}`,
      type: 'stat_card',
      title: `Agent Response to "${this.userInput()}"`,
      content: `A2UI Schema synthesized: Rendered dynamic interactive component for input.`,
      timestamp: new Date().toLocaleTimeString(),
      metadata: { query: this.userInput(), status: 'SUCCESS' }
    };

    setTimeout(() => {
      this.cards.update((prev) => [newCard, ...prev]);
      this.userInput.set('');
      this.agentStatus.set('connected');
    }, 400);
  }
}
