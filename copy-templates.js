const fs = require('fs-extra');
const path = require('path');

const ignoreList = [
  'node_modules',
  'dist',
  '.angular',
  '.vite',
  '__pycache__',
  '.venv',
  '.env'
];

const filterFunc = (src, dest) => {
  const basename = path.basename(src);
  // Also check if the path ends with any of the ignore list
  return !ignoreList.includes(basename);
};

console.log("Copying templates (ignoring node_modules, dist, etc.)...");
fs.copySync('templates', 'dist/templates', { filter: filterFunc });
console.log("Templates copied successfully!");
