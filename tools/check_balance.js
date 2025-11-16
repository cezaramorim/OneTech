const fs = require('fs');
const path = require('path');
const file = path.resolve(__dirname, '..', 'static', 'js', 'povoamento_lotes.js');
const s = fs.readFileSync(file, 'utf8');
let stack = [];
const opens = { '(': ')', '{': '}', '[': ']' };
const closes = { ')': '(', '}': '{', ']': '[' };
for (let i = 0; i < s.length; i++) {
  const ch = s[i];
  if (opens[ch]) {
    stack.push({ ch, pos: i });
  } else if (closes[ch]) {
    const last = stack[stack.length - 1];
    if (last && last.ch === closes[ch]) {
      stack.pop();
    } else {
      // compute line/col
      const upTo = s.slice(0, i);
      const lines = upTo.split(/\r?\n/);
      const line = lines.length;
      const col = lines[lines.length - 1].length + 1;
      console.log(`Mismatch: found '${ch}' at index ${i} (line ${line}, col ${col}) but top of stack is ${last ? `'${last.ch}' at index ${last.pos}` : "<empty>"}`);
      process.exit(0);
    }
  }
}
if (stack.length) {
  const last = stack[stack.length - 1];
  const upTo = s.slice(0, last.pos);
  const lines = upTo.split(/\r?\n/);
  const line = lines.length;
  const col = lines[lines.length - 1].length + 1;
  console.log(`Unclosed '${last.ch}' opened at index ${last.pos} (line ${line}, col ${col})`);
} else {
  console.log('All balanced');
}
