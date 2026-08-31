import { Component, input, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AgentStatus } from '../../models/chat.types';

@Component({
  selector: 'app-chat-header',
  standalone: true,
  imports: [CommonModule],
  template: `
    <header class="app-header">
      <div class="brand-group">
        <div class="logo-icon">
          <svg class="adk-logo" viewBox="0 0 24 24" width="28" height="28">
            <path
              fill="#1a73e8"
              d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"
            />
          </svg>
        </div>
        <div class="title-details">
          <h1>{{ title() }}</h1>
        </div>
      </div>
      <div class="status-indicator">
        <span class="status-dot" [ngClass]="status()"></span>
        <span class="status-label">Agent: {{ status() | uppercase }}</span>
      </div>
    </header>
  `,
  styles: [`
    .app-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 28px;
      background: #ffffff;
      border-bottom: 1px solid var(--google-grey-200, #e8eaed);
      box-shadow: 0 1px 2px rgba(60, 64, 67, 0.04);
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .logo-icon {
      font-size: 28px;
    }

    .title-details h1 {
      margin: 0;
      font-size: 19px;
      font-weight: 700;
      color: var(--google-grey-900, #202124);
      letter-spacing: -0.2px;
    }

    .status-indicator {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 12px;
      font-weight: 600;
      background: #ffffff;
      padding: 6px 14px;
      border-radius: 100px;
      border: 1px solid var(--google-grey-300, #dadce0);
      box-shadow: 0 1px 2px rgba(60, 64, 67, 0.04);
    }

    .status-dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
    }

    .status-dot.connected {
      background: var(--google-green, #34a853);
    }

    .status-dot.executing {
      background: var(--google-yellow, #f9ab00);
      animation: pulse 1s infinite;
    }

    .status-dot.idle {
      background: var(--google-grey-500, #9aa0a6);
    }

    @keyframes pulse {
      0% { opacity: 1; }
      50% { opacity: 0.35; }
      100% { opacity: 1; }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatHeaderComponent {
  title = input<string>('Weather Agent UI');
  status = input<AgentStatus>('connected');
}
