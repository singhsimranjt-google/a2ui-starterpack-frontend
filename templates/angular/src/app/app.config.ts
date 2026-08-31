import { ApplicationConfig } from '@angular/core';
import {
  A2UI_RENDERER_CONFIG,
  A2uiRendererService,
  provideMarkdownRenderer
} from '@a2ui/angular/v0_9';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { MaterialBasicCatalog } from './catalogs/material-basic-catalog';

export const appConfig: ApplicationConfig = {
  providers: [
    {
      provide: A2UI_RENDERER_CONFIG,
      useFactory: () => ({
        catalogs: [new MaterialBasicCatalog()],
        actionHandler: (action: any) => {
          console.log('[A2UI Action received]:', action);
        },
      }),
    },
    A2uiRendererService,
    provideMarkdownRenderer(async (text: string) =>
      DOMPurify.sanitize(marked.parse(text, { async: false }) as string)
    ),
  ],
};
