import { Pipe, PipeTransform } from '@angular/core';
import { marked } from 'marked';
import DOMPurify from 'dompurify';

@Pipe({
  name: 'markdown',
  standalone: true,
})
export class MarkdownPipe implements PipeTransform {
  transform(value: string | undefined | null): string {
    if (!value) return '';
    try {
      const rawHtml = marked.parse(value, { async: false }) as string;
      return DOMPurify.sanitize(rawHtml);
    } catch (err) {
      console.error('Markdown parsing failed:', err);
      return value;
    }
  }
}
