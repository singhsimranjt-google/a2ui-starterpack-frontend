import { Component, ChangeDetectionStrategy, input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-agent-loader',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="message-row agent">
      <div class="sender-info">
        <span class="sender-name">{{ name() }}</span>
        <span class="thinking-label">Thinking...</span>
      </div>

      <div class="message-bubble-wrapper agent loader-bubble">
        <div class="avatar agent">
          <svg class="adk-agent-avatar rotating" viewBox="0 0 24 24" width="22" height="22">
            <defs>
              <linearGradient id="adkLoaderGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stop-color="#1a73e8" />
                <stop offset="60%" stop-color="#4285f4" />
                <stop offset="100%" stop-color="#34a853" />
              </linearGradient>
            </defs>
            <path fill="url(#adkLoaderGrad)" d="M19 9l1.25-2.75L23 5l-2.75-1.25L19 1l-1.25 2.75L15 5l2.75 1.25L19 9zm-7.5.5L9 4 6.5 9.5 1 12l5.5 2.5L9 20l2.5-5.5L17 12l-5.5-2.5zM19 15l-1.25 2.75L15 19l2.75 1.25L19 23l1.25-2.75L23 19l-2.75-1.25L19 15z"/>
          </svg>
        </div>

        <div class="loader-container">
          <div class="dot dot-blue"></div>
          <div class="dot dot-red"></div>
          <div class="dot dot-yellow"></div>
          <div class="dot dot-green"></div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }

    .message-row {
      display: flex;
      flex-direction: column;
      gap: 5px;
      width: 100%;
      max-width: 800px;
      margin: 0 auto;
      align-items: flex-start;
    }

    .sender-info {
      display: flex;
      gap: 8px;
      font-size: 12px;
      color: var(--google-grey-700, #5f6368);
      font-weight: 500;
      padding: 0 4px;
    }

    .thinking-label {
      color: var(--google-blue, #1a73e8);
      font-weight: 500;
      font-size: 11.5px;
      font-style: italic;
    }

    .message-bubble-wrapper {
      display: flex;
      gap: 12px;
      max-width: 100%;
      width: 100%;
      align-items: flex-start;
    }

    .avatar {
      width: 38px;
      height: 38px;
      border-radius: 50%;
      background: #ffffff;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 1px 3px rgba(60, 64, 67, 0.12), 0 1px 2px rgba(60, 64, 67, 0.08);
      flex-shrink: 0;
      border: 1px solid var(--google-grey-200, #e8eaed);
    }

    .loader-container {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 14px 20px;
      background: #ffffff;
      border-radius: 20px;
      border-bottom-left-radius: 4px;
      width: fit-content;
      border: 1px solid var(--google-grey-200, #e8eaed);
      box-shadow: 0 1px 2px rgba(60, 64, 67, 0.05);
    }

    .dot {
      width: 9px;
      height: 9px;
      border-radius: 50%;
      animation: google-bounce 1.4s infinite ease-in-out both;
    }

    .dot.dot-blue {
      background-color: var(--google-blue, #1a73e8);
      animation-delay: -0.32s;
    }

    .dot.dot-red {
      background-color: var(--google-red, #ea4335);
      animation-delay: -0.16s;
    }

    .dot.dot-yellow {
      background-color: var(--google-yellow, #f9ab00);
      animation-delay: 0s;
    }

    .dot.dot-green {
      background-color: var(--google-green, #34a853);
      animation-delay: 0.16s;
    }

    @keyframes google-bounce {
      0%, 80%, 100% {
        transform: scale(0.5);
        opacity: 0.4;
      }
      40% {
        transform: scale(1.15);
        opacity: 1;
      }
    }

    .adk-agent-avatar.rotating {
      animation: gentle-spin 3s linear infinite;
    }

    @keyframes gentle-spin {
      0% { transform: rotate(0deg); }
      50% { transform: rotate(180deg) scale(1.08); }
      100% { transform: rotate(360deg); }
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AgentLoaderComponent {
  name = input<string>('Agent');
}
