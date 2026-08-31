import {
  Component,
  computed,
  ChangeDetectionStrategy,
  Injectable,
  inject
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import {
  BasicCatalogBase,
  CatalogComponent,
  ComponentHostComponent,
  A2uiRendererService
} from '@a2ui/angular/v0_9';
import { CardApi, ButtonApi, DividerApi, DataContext } from '@a2ui/web_core/v0_9';

/**
 * Bespoke Angular Material Card wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-card',
  standalone: true,
  imports: [MatCardModule, ComponentHostComponent],
  template: `
    <mat-card appearance="outlined" class="a2ui-material-card">
      <mat-card-content>
        @if (child()) {
          <a2ui-v09-component-host [componentKey]="child()!" [surfaceId]="surfaceId()">
          </a2ui-v09-component-host>
        }
      </mat-card-content>
    </mat-card>
  `,
  styles: [`
    .a2ui-material-card {
      width: 100% !important;
      border-radius: var(--a2ui-card-border-radius, 24px) !important;
      background: var(--a2ui-card-background, #ffffff) !important;
      box-shadow: var(--a2ui-card-box-shadow) !important;
      border: var(--a2ui-card-border, 1px solid #e0e3e7) !important;
      padding: 6px 10px !important;
      box-sizing: border-box !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialCardComponent extends CatalogComponent<typeof CardApi> {
  child = computed(() => this.props()['child']?.value());
}

/**
 * Bespoke Angular Material Button wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-button',
  standalone: true,
  imports: [MatButtonModule, ComponentHostComponent],
  template: `
    <button
      mat-flat-button
      [color]="variant() === 'primary' ? 'primary' : undefined"
      [disabled]="props()['isValid'].value() === false"
      (click)="handleClick()"
      class="a2ui-material-button"
    >
      @if (child()) {
        <a2ui-v09-component-host [componentKey]="child()!" [surfaceId]="surfaceId()">
        </a2ui-v09-component-host>
      }
    </button>
  `,
  styles: [`
    .a2ui-material-button {
      border-radius: 100px !important;
      font-family: var(--font-family-sans, 'Google Sans', sans-serif);
      font-weight: 500;
      padding: 0 20px !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialButtonComponent extends CatalogComponent<typeof ButtonApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  variant = computed(() => this.props()['variant']?.value() || 'primary');
  child = computed(() => this.props()['child']?.value());

  handleClick() {
    const action = this.props()['action']?.value();
    if (action) {
      const surface = this.surface();
      if (surface) {
        const dataContext = new DataContext(surface, this.dataContextPath());
        const resolvedAction = dataContext.resolveAction(action);
        surface.dispatchAction(resolvedAction, this.componentId());
      }
    }
  }
}

/**
 * Bespoke Angular Material Divider wrapper for A2UI Basic Catalog
 */
@Component({
  selector: 'a2ui-mat-divider',
  standalone: true,
  imports: [MatDividerModule],
  template: `<mat-divider class="a2ui-material-divider"></mat-divider>`,
  styles: [`
    .a2ui-material-divider {
      margin: 14px 0 !important;
      border-top-color: var(--google-grey-200, #e8eaed) !important;
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialDividerComponent extends CatalogComponent<typeof DividerApi> {}

/**
 * Bespoke Angular Material Extended Catalog for A2UI v0.9
 */
@Injectable({
  providedIn: 'root',
})
export class MaterialBasicCatalog extends BasicCatalogBase {
  constructor() {
    super({
      components: {
        card: { ...CardApi, component: MaterialCardComponent },
        button: { ...ButtonApi, component: MaterialButtonComponent },
        divider: { ...DividerApi, component: MaterialDividerComponent },
      },
    });
  }
}
