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
import { MatIconModule } from '@angular/material/icon';
import { MatSelectModule } from '@angular/material/select';
import { MatTimepickerModule } from '@angular/material/timepicker';

import { MatCheckboxModule } from '@angular/material/checkbox';
import { FormsModule } from '@angular/forms';

import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';

import {
  BasicCatalogBase,
  CatalogComponent,
  ComponentHostComponent,
  A2uiRendererService
} from '@a2ui/angular/v0_9';
import { CardApi, ButtonApi, DividerApi, DataContext, TextFieldApi, CheckBoxApi, RowApi, IconApi, DateTimeInputApi, ImageApi, ChoicePickerApi } from '@a2ui/web_core/v0_9';

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
  imports: [ComponentHostComponent],
  template: `
    <button
      [disabled]="props()['isValid']?.value() === false"
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
      border-radius: 4px !important;
      font-family: var(--font-family-sans, 'Google Sans', sans-serif);
      font-size: 14px;
      font-weight: 500;
      padding: 10px 20px !important;
      background-color: #1a73e8 !important; /* Official Google Blue */
      border: none !important;
      cursor: pointer;
      box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15) !important;
      transition: box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
    }
    
    /* VERY IMPORTANT: ::ng-deep pierces Angular's view encapsulation to target the child Text component */
    .a2ui-material-button ::ng-deep * {
      color: #ffffff !important; 
    }

    .a2ui-material-button:hover:not(:disabled) {
      box-shadow: 0 1px 3px 0 rgba(60,64,67,0.3), 0 4px 8px 3px rgba(60,64,67,0.15) !important;
      background-color: #1557b0 !important; /* Darker blue on hover */
    }

    .a2ui-material-button:disabled {
      background-color: #cccccc !important;
      box-shadow: none !important;
      cursor: not-allowed;
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
export class MaterialDividerComponent extends CatalogComponent<typeof DividerApi> { }

/**
 * textfield a2ui
 */
@Component({
  selector: 'a2ui-mat-textfield',
  standalone: true,
  imports: [FormsModule],
  template: `
    <div class="a2ui-textfield-container">
      <label class="a2ui-textfield-label">{{ label() }}</label>
      <input 
        type="text" 
        [ngModel]="value()" 
        (ngModelChange)="onValueChange($event)"
        class="a2ui-textfield-input"
      >
    </div>
  `,
  styles: [`
    .a2ui-textfield-container {
      width: 100%;
      margin-bottom: 12px;
      display: flex;
      flex-direction: column;
    }
    .a2ui-textfield-label {
      font-size: 12px;
      font-weight: bold;
      margin-bottom: 4px;
      font-family: sans-serif;
      color: #333333 !important;
    }
    .a2ui-textfield-input {
      padding: 12px !important;
      border: 1px solid #000000 !important;
      border-radius: 4px !important;
      
      /* Force browser dark-mode engines to back off */
      color-scheme: light !important;
      background: #ffffff !important;
      color: #000000 !important;
      -webkit-appearance: none !important;
      appearance: none !important;
      
      font-size: 16px !important;
      font-family: sans-serif !important;
      box-sizing: border-box !important;
      outline: none !important;
    }
    .a2ui-textfield-input:focus {
      border: 2px solid #1a73e8 !important;
      padding: 11px !important; /* Adjust padding to prevent jumping when border gets thicker */
    }
  `],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialTextFieldComponent extends CatalogComponent<typeof TextFieldApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  label = computed(() => this.props()['label']?.value() || '');
  value = computed(() => this.props()['value']?.value() || '');

  inputType = computed(() => {
    return this.label().toLowerCase().includes('date') ? 'date' : 'text';
  });

  onValueChange(newValue: string) {
    // const surface = this.surface();
    // if (surface) {
    //   const path = (this.props()['value'] as any).path();
    //   if (path) surface.dataModel.set(path, newValue);
    // }
    this.props()['value']?.onUpdate(newValue);
  }
}

/**
 * checkbox a2ui
 */
@Component({
  selector: 'a2ui-mat-checkbox',
  standalone: true,
  imports: [MatCheckboxModule, FormsModule],
  template: `
    <mat-checkbox [ngModel]="value()" (ngModelChange)="onValueChange($event)" style="margin-bottom: 12px;">
      {{ label() }}
    </mat-checkbox>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialCheckboxComponent extends CatalogComponent<typeof CheckBoxApi> {
  private rendererService = inject(A2uiRendererService);
  surface = computed(() => this.rendererService.surfaceGroup.getSurface(this.surfaceId()));

  label = computed(() => this.props()['label']?.value() || '');
  value = computed(() => {
    const val = this.props()['value']?.value() as any;
    return val === 'true' || val === true;
  });

  onValueChange(newValue: boolean) {
    const surface = this.surface();
    if (surface) {
      // const path = (this.props()['value'] as any).path();
      // if (path) surface.dataModel.set(path, newValue);
      this.props()['value']?.onUpdate(newValue);
    }
  }
}

/**
 * Bespoke Angular wrapper for A2UI Row Component
 */
@Component({
  selector: 'a2ui-mat-row',
  standalone: true,
  imports: [ComponentHostComponent],
  template: `
    <div style="display: flex; flex-direction: row; align-items: center; gap: 24px;">
      @for (child of children(); track $index) {
        <!-- The critical fix: wrapping the host in a native div -->
        <div style="display: block;">
          <a2ui-v09-component-host [componentKey]="child" [surfaceId]="surfaceId()">
          </a2ui-v09-component-host>
        </div>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialRowComponent extends CatalogComponent<typeof RowApi> {
  children = computed(() => this.props()['children']?.value() || []);
}

/**
 * Official Angular Material Datepicker wrapped for A2UI
 */
@Component({
  selector: 'a2ui-mat-datetime',
  standalone: true,
  imports: [
    MatFormFieldModule,
    MatInputModule,
    MatDatepickerModule,
    MatTimepickerModule,
    MatNativeDateModule,
    FormsModule,
  ],
  template: `
    <div style="display: flex; gap: 12px; width: 100%;">
      @if (showDate()) {
        <mat-form-field appearance="outline" style="flex: 1; margin-bottom: 12px;">
          <mat-label>{{ label() || 'Pick a date' }}</mat-label>
          <input matInput [matDatepicker]="datePicker"
                 [ngModel]="dateValue()" (ngModelChange)="onDateChange($event)">
          <mat-datepicker-toggle matIconSuffix [for]="datePicker"></mat-datepicker-toggle>
          <mat-datepicker #datePicker></mat-datepicker>
        </mat-form-field>
      }
      @if (showTime()) {
        <mat-form-field appearance="outline" style="flex: 1; margin-bottom: 12px;">
          <mat-label>{{ label() || 'Pick a time' }}</mat-label>
          <input matInput [matTimepicker]="timePicker"
                 [ngModel]="timeValue()" (ngModelChange)="onTimeChange($event)">
          <mat-timepicker-toggle matIconSuffix [for]="timePicker"></mat-timepicker-toggle>
          <mat-timepicker #timePicker interval="30min"></mat-timepicker>
        </mat-form-field>
      }
    </div>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialDateTimeInputComponent extends CatalogComponent<typeof DateTimeInputApi> {
  label = computed(() => this.props()['label']?.value() || '');

  showTime = computed(() => this.props()['enableTime']?.value() === true);
  // Back-compat: if neither flag is set, behave as a plain date picker
  showDate = computed(
    () => this.props()['enableDate']?.value() === true || !this.showTime()
  );

  private raw = computed(() => String(this.props()['value']?.value() ?? ''));

  // Accepts "2026-09-18", "2026-09-18T14:30", "2026-09-18T14:30:00.000Z"
  dateValue = computed<Date | null>(() => {
    const m = this.raw().match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!m) return null;
    return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  });

  // Accepts "14:30" or the time portion of a full ISO string
  timeValue = computed<Date | null>(() => {
    const m = this.raw().match(/(?:^|T)(\d{2}):(\d{2})/);
    if (!m) return null;
    const base = this.dateValue() ?? new Date();
    const out = new Date(base);
    out.setHours(Number(m[1]), Number(m[2]), 0, 0);
    return out;
  });

  onDateChange(newValue: any) {
    const d = this.toDate(newValue);
    if (!d) return;
    this.commit(d, this.showTime() ? this.timeValue() : null);
  }

  onTimeChange(newValue: any) {
    const t = this.toDate(newValue);
    if (!t) return;
    this.commit(this.showDate() ? this.dateValue() : null, t);
  }

  private toDate(v: any): Date | null {
    if (!v) return null;
    const d = v instanceof Date ? v : new Date(v);
    return isNaN(d.getTime()) ? null : d;
  }

  /** Emits YYYY-MM-DD, HH:MM, or YYYY-MM-DDTHH:MM depending on which fields are on. */
  /** Emits YYYY-MM-DD for date-only, or full ISO YYYY-MM-DDTHH:MM:00 whenever a time is set. */
  private commit(date: Date | null, time: Date | null) {
    const pad = (n: number) => String(n).padStart(2, '0');

    // A time-only field still needs a date anchor, or datetime.fromisoformat() rejects it
    const d = date ?? (time ? new Date() : null);
    const datePart = d
      ? `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
      : '';
    const timePart = time
      ? `${pad(time.getHours())}:${pad(time.getMinutes())}:00`
      : '';

    const out = timePart ? `${datePart}T${timePart}` : datePart;
    this.props()['value']?.onUpdate(out);
  }
}

/**
 * A2UI catalog Icon names -> Material Icons ligature names.
 * Kept identical to the React catalog so both frontends render the same glyph.
 */
const ICON_LIGATURE_OVERRIDES: Record<string, string> = {
  play: 'play_arrow',
  rewind: 'fast_rewind',
  favoriteOff: 'favorite_border',
  starOff: 'star_border',
};

/**
 * Bespoke Angular wrapper for A2UI Icon Component
 */
@Component({
  selector: 'a2ui-mat-icon',
  standalone: true,
  imports: [MatIconModule],
  template: `<mat-icon style="display: flex; justify-content: center; align-items: center; width: 24px; height: 24px;">{{ ligature() }}</mat-icon>`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialIconComponent extends CatalogComponent<typeof IconApi> {
  name = computed(() => this.props()['name']?.value() || '');

  // The Material Icons ligature font expects snake_case (locationOn -> location_on).
  // Without this, 24 of the 59 catalog icons render as raw text in Angular.
  ligature = computed(() => {
    const raw = String(this.name() ?? '');
    return ICON_LIGATURE_OVERRIDES[raw] ?? raw.replace(/[A-Z]/g, (l) => `_${l.toLowerCase()}`);
  });
}


/**
 * Bespoke Angular wrapper for A2UI Image Component
 */
@Component({
  selector: 'a2ui-mat-image',
  standalone: true,
  template: `<img [src]="url()" style="width: 100%; max-height: 200px; object-fit: cover; border-radius: 8px; margin-bottom: 12px;" />`,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialImageComponent extends CatalogComponent<any> {
  url = computed(() => this.props()['url']?.value() || '');
}


/**
 * Bespoke Angular Material <mat-select> dropdown for A2UI ChoicePicker.
 * Renders as a real dropdown instead of the default radio/checkbox list.
 */
@Component({
  selector: 'a2ui-mat-choicepicker',
  standalone: true,
  imports: [MatFormFieldModule, MatSelectModule, FormsModule],
  template: `
    <mat-form-field appearance="outline" style="width: 100%; margin-bottom: 12px;">
      <mat-label>{{ label() }}</mat-label>
      <mat-select
        [multiple]="isMultiple()"
        [ngModel]="isMultiple() ? selected() : selected()[0]"
        (ngModelChange)="onValueChange($event)">
        @for (opt of options(); track opt.value) {
          <mat-option [value]="opt.value">{{ opt.label }}</mat-option>
        }
      </mat-select>
    </mat-form-field>
  `,
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class MaterialChoicePickerComponent extends CatalogComponent<typeof ChoicePickerApi> {
  label = computed(() => this.props()['label']?.value() || '');

  // "multipleSelection" -> multi-select dropdown; default is single-select
  isMultiple = computed(
    () => this.props()['variant']?.value() === 'multipleSelection'
  );

  options = computed(() => {
    const raw = (this.props()['options']?.value() as any) || [];
    if (!Array.isArray(raw)) return [];
    return raw.map((o: any) => ({
      value: String(o?.value ?? ''),
      // label may arrive as a plain string or a resolved DynamicString
      label: String(
        typeof o?.label === 'object' ? (o?.label?.value ?? o?.value) : (o?.label ?? o?.value)
      ),
    }));
  });

  // A2UI binds ChoicePicker.value to a string ARRAY, even when single-select
  selected = computed<string[]>(() => {
    const val = this.props()['value']?.value() as any;
    if (Array.isArray(val)) return val.map(String);
    if (val === undefined || val === null || val === '') return [];
    return [String(val)];
  });

  onValueChange(newValue: string | string[]) {
    const next = Array.isArray(newValue) ? newValue : newValue ? [newValue] : [];
    this.props()['value']?.onUpdate(next);
  }
}


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
        dateTimeInput: { ...DateTimeInputApi, component: MaterialDateTimeInputComponent },
        textField: { ...TextFieldApi, component: MaterialTextFieldComponent },
        checkBox: { ...CheckBoxApi, component: MaterialCheckboxComponent },
        choicePicker: { ...ChoicePickerApi, component: MaterialChoicePickerComponent },
        row: { ...RowApi, component: MaterialRowComponent },
        icon: { ...IconApi, component: MaterialIconComponent },
      },
      extraComponents: [
        { ...ImageApi, component: MaterialImageComponent }
      ]
    });
  }
}
