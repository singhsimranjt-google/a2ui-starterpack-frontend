const fs = require('fs-extra');
const path = require('path');

// Never ship build artefacts, virtualenvs, caches, or secrets.
const IGNORED = new Set([
  'node_modules', 'dist', '.angular', '.vite', '.next',
  '__pycache__', '.venv', 'venv', '.pytest_cache', '.mypy_cache',
  '.env', '.adk', '.DS_Store', '.git'
]);

const filterFunc = (src) => {
  const base = path.basename(src);
  if (IGNORED.has(base)) return false;
  if (base.endsWith('.pyc')) return false;
  if (base.startsWith('.env.') && base !== '.env.example') return false;
  return true;
};

const copy = (from, to) => {
  if (!fs.existsSync(from)) {
    console.error(`  ✗ MISSING: ${from}`);
    process.exitCode = 1;
    return;
  }
  fs.copySync(from, to, { filter: filterFunc });
  console.log(`  ✓ ${from}  ->  ${to}`);
};

// ---------------------------------------------------------------------------
// 1. Static templates the user receives verbatim.
//    Source of truth is root_agent/. The destination names must match each
//    generator's `templateSubdir` value.
// ---------------------------------------------------------------------------
console.log('Copying static templates...');
copy('templates/frontend/angular', 'dist/templates/angular');           // AngularGenerator
copy('templates/frontend/react', 'dist/templates/react');             // ReactGenerator
copy('templates/fullstack-root', 'dist/templates/fullstack-root');    // FullStackGenerator

// ---------------------------------------------------------------------------
// 2. Meta-agent toolchain - staging inputs only, never copied into a project
// ---------------------------------------------------------------------------
console.log('Bundling meta-agent toolchain...');

const META = 'dist/templates/meta';

copy('templates/backend/root_agent.py', `${META}/adk-a2ui/root_agent.py`);
copy('templates/backend/basic_template', `${META}/adk-a2ui/basic_template`);
copy('templates/backend/pyproject.toml', `${META}/adk-a2ui/pyproject.toml`);

copy('templates/gemini_enterprise/root_agent.py', `${META}/gemini-enterprise/root_agent.py`);
copy('templates/gemini_enterprise/ge_template', `${META}/gemini-enterprise/ge_template`);
copy('templates/gemini_enterprise/ge_template/pyproject.toml', `${META}/gemini-enterprise/pyproject.toml`);

// ---------------------------------------------------------------------------
// 3. Safety net - fail the build rather than publish a secret
// ---------------------------------------------------------------------------
const leaked = [];
(function scan(dir) {
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) scan(p);
    else if (e.name === '.env' || e.name.endsWith('.pem')) leaked.push(p);
  }
})('dist');

if (leaked.length) {
  console.error('\n✗ BUILD ABORTED - credential files found in dist/:');
  leaked.forEach(f => console.error(`    ${f}`));
  process.exit(1);
}

console.log('\nTemplates bundled successfully.');
