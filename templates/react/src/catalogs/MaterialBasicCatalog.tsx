import React from 'react';
import { Card, CardContent, Typography, Button, Divider, Box } from '@mui/material';
import { basicCatalog, createBinderlessComponentImplementation } from '@a2ui/react/v0_9';
import { CardApi, ColumnApi, RowApi, TextApi, ButtonApi, DividerApi, IconApi } from '@a2ui/web_core/v0_9';

// 1. Map Card
const MaterialCard = createBinderlessComponentImplementation(CardApi, ({ context, buildChild }) => {
  const childKey = context.componentModel.properties.child;
  const childrenKeys = context.componentModel.properties.children || [];

  return (
    <Card variant="outlined" sx={{
      mb: 2,
      width: '100%',
      maxWidth: '100%',
      borderRadius: 'var(--a2ui-card-border-radius, 24px)',
      background: 'var(--a2ui-card-background, #ffffff)',
      boxShadow: 'var(--a2ui-card-box-shadow)',
      border: 'var(--a2ui-card-border, 1px solid #e0e3e7)'
    }}>
      <CardContent>
        {childKey && buildChild(childKey)}
        {childrenKeys.map((key) => <React.Fragment key={key}>{buildChild(key)}</React.Fragment>)}
      </CardContent>
    </Card>
  );
});

// 2. Map Column
const MaterialColumn = createBinderlessComponentImplementation(ColumnApi, ({ context, buildChild }) => {
  const childrenKeys = context.componentModel.properties.children || [];
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      {childrenKeys.map((key) => <React.Fragment key={key}>{buildChild(key)}</React.Fragment>)}
    </Box>
  );
});

// 3. Map Row
const MaterialRow = createBinderlessComponentImplementation(RowApi, ({ context, buildChild }) => {
  const childrenKeys = context.componentModel.properties.children || [];
  return (
    <Box sx={{ display: 'flex', flexDirection: 'row', gap: 1, alignItems: 'center' }}>
      {childrenKeys.map((key) => <React.Fragment key={key}>{buildChild(key)}</React.Fragment>)}
    </Box>
  );
});

// 4. Map Text
const MaterialText = createBinderlessComponentImplementation(TextApi, ({ context }) => {
  const text = context.componentModel.properties.text || '';
  const usageHint = context.componentModel.properties.usageHint || 'body';

  let variant: any = 'body1';
  if (usageHint === 'h1') variant = 'h4';
  if (usageHint === 'h2') variant = 'h5';
  if (usageHint === 'h3') variant = 'h6';
  if (usageHint === 'caption') variant = 'caption';

  return <Typography variant={variant} className={`a2ui-text ${usageHint}`}>{text}</Typography>;
});

// 5. Map Button
const MaterialButton = createBinderlessComponentImplementation(ButtonApi, ({ context }) => {
  const label = context.componentModel.properties.label || 'Button';
  const action = context.componentModel.properties.action;
  const variant = context.componentModel.properties.variant === 'outlined' ? 'outlined' : 'contained';

  return (
    <Button
      variant={variant}
      onClick={() => action && context.surface.dispatchAction(action, context.componentModel.id)}
    >
      {label}
    </Button>
  );
});

// 6. Map Divider
const MaterialDivider = createBinderlessComponentImplementation(DividerApi, () => {
  return <Divider sx={{ my: 1 }} />;
});

// 7. Map Icon

// The Catalog Definition explicitly mapping to React functional components

const MaterialIcon = createBinderlessComponentImplementation(IconApi, ({ context }) => {
  // Get the string name from the model
  let iconName = context.componentModel.properties.name || '';
  if (typeof iconName !== 'string') {
    iconName = String(iconName);
  }
  // Convert camelCase (locationOn) to snake_case (location_on)
  const snakeName = iconName.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`);

  // Use material-icons class
  return <span className="material-icons a2ui-icon" style={{ color: 'var(--google-blue)' }}>{snakeName}</span>;
});

export const materialCatalog = {
  ...basicCatalog,
  components: new Map([
    ...basicCatalog.components,
    [IconApi.name, MaterialIcon],
    [CardApi.name, MaterialCard],
    [ColumnApi.name, MaterialColumn],
    [RowApi.name, MaterialRow],
    [TextApi.name, MaterialText],
    [ButtonApi.name, MaterialButton],
    [DividerApi.name, MaterialDivider],

  ])
};
