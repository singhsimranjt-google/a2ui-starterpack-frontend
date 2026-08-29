import pc from 'picocolors';

export function printBanner(): void {
  console.log();
  console.log(pc.cyan('  ┌────────────────────────────────────────────────────────┐'));
  console.log(pc.cyan('  │') + pc.bold(pc.white('                goog-adk-a2ui-starter                   ')) + pc.cyan('│'));
  console.log(pc.cyan('  │') + pc.dim('   Scaffolding Angular, React, Python & GE UI Agents    ') + pc.cyan('│'));
  console.log(pc.cyan('  └────────────────────────────────────────────────────────┘'));
  console.log();
}
