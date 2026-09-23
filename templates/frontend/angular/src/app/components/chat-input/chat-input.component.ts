import { Component, input, output, signal, ChangeDetectionStrategy } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="input-container">
      <div class="input-bar">
        <input
          type="text"
          [(ngModel)]="inputText"
          (keyup.enter)="handleSend()"
          placeholder="Say 'Hi' to see the A2UI Agent response..."
          [disabled]="disabled()"
        />
        <button
          (click)="handleSend()"
          [disabled]="disabled() || !inputText().trim()"
          class="send-btn"
        >
          {{ disabled() ? 'Checking...' : 'Send' }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host {
      display: block;
      width: 100%;
    }

    .input-container {
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #ffffff;
      padding: 16px 20px;
      border-radius: 24px;
      box-shadow: 0 1px 3px rgba(60, 64, 67, 0.08), 0 4px 12px rgba(60, 64, 67, 0.05);
      border: 1px solid var(--google-grey-200, #e8eaed);
      width: 100%;
      max-width: 800px;
      margin: 0 auto;
      box-sizing: border-box;
    }

    .input-bar {
      display: flex;
      gap: 10px;
    }

    .input-bar input {
      flex: 1;
      padding: 13px 18px;
      border: 1px solid var(--google-grey-300, #dadce0);
      border-radius: 100px;
      font-size: 14.5px;
      outline: none;
      background: var(--google-bg, #f8fafd);
      color: var(--google-grey-900, #202124);
      transition: all 0.2s ease;
    }

    .input-bar input:focus {
      border-color: var(--google-blue, #1a73e8);
      background: #ffffff;
      box-shadow: 0 0 0 3px rgba(26, 115, 232, 0.15);
    }

    .send-btn {
      background: var(--google-blue, #1a73e8);
      color: #ffffff;
      border: none;
      padding: 0 26px;
      border-radius: 100px;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
      box-shadow: 0 1px 3px rgba(26, 115, 232, 0.25);
    }

    .send-btn:hover {
      background: var(--google-blue-dark, #1557b0);
      box-shadow: 0 2px 6px rgba(26, 115, 232, 0.35);
    }

    .send-btn:disabled {
      background: var(--google-grey-300, #dadce0);
      color: var(--google-grey-500, #9aa0a6);
      cursor: not-allowed;
      box-shadow: none;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ChatInputComponent {
  disabled = input<boolean>(false);
  sendMessage = output<string>();

  inputText = signal('');

  handleSend() {
    const text = this.inputText().trim();
    if (!text || this.disabled()) return;
    this.sendMessage.emit(text);
    this.inputText.set('');
  }
}
