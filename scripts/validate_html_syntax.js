#!/usr/bin/env node

const fs = require('node:fs');
const path = require('node:path');
const Babel = require(path.resolve(__dirname, '..', 'assets', 'cdn', 'babel.min.js'));

const VOID_ELEMENTS = new Set([
  'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
  'link', 'meta', 'param', 'source', 'track', 'wbr',
]);
const JAVASCRIPT_TYPES = new Set([
  '', 'application/javascript', 'application/x-javascript', 'module',
  'text/babel', 'text/javascript', 'text/jsx',
]);

function usage() {
  console.log('Usage: node scripts/validate_html_syntax.js <html> [<html> ...]');
  console.log('Checks generated HTML structure and compiles inline JavaScript/JSX without executing it.');
}

function attributeValue(attributes, name) {
  const pattern = new RegExp(`\\b${name}\\s*=\\s*(["'])(.*?)\\1`, 'i');
  const match = pattern.exec(attributes);
  return match ? match[2].trim() : null;
}

function blankRawContent(source, tagName) {
  const pattern = new RegExp(`(<${tagName}\\b[^>]*>)([\\s\\S]*?)(<\\/${tagName}\\s*>)`, 'gi');
  return source.replace(pattern, (_, open, body, close) => {
    return `${open}${body.replace(/[^\r\n]/g, ' ')}${close}`;
  });
}

function validateHtmlStructure(source) {
  const errors = [];
  const openScripts = (source.match(/<script\b/gi) || []).length;
  const closeScripts = (source.match(/<\/script\s*>/gi) || []).length;
  if (openScripts !== closeScripts) {
    errors.push(`script tag count differs: ${openScripts} opening, ${closeScripts} closing`);
  }

  let sanitized = source.replace(/<!--[\s\S]*?-->/g, (comment) => comment.replace(/[^\r\n]/g, ' '));
  sanitized = blankRawContent(blankRawContent(sanitized, 'script'), 'style');

  const stack = [];
  const seen = new Set();
  const tagPattern = /<\/?([A-Za-z][\w:-]*)\b[^>]*>/g;
  let match;
  while ((match = tagPattern.exec(sanitized)) !== null) {
    const token = match[0];
    const tag = match[1].toLowerCase();
    const line = source.slice(0, match.index).split(/\r?\n/).length;
    const isClosing = /^<\//.test(token);
    const isSelfClosing = /\/\s*>$/.test(token);
    seen.add(tag);

    if (isClosing) {
      const current = stack.at(-1);
      if (!current) {
        errors.push(`line ${line}: closing </${tag}> has no matching opening tag`);
      } else if (current.tag !== tag) {
        errors.push(`line ${line}: closing </${tag}> does not match <${current.tag}> opened at line ${current.line}`);
      } else {
        stack.pop();
      }
    } else if (!isSelfClosing && !VOID_ELEMENTS.has(tag)) {
      stack.push({ tag, line });
    }
  }

  for (const item of stack.reverse()) {
    errors.push(`line ${item.line}: <${item.tag}> is not closed`);
  }
  for (const required of ['html', 'head', 'body']) {
    if (!seen.has(required)) errors.push(`missing <${required}> element`);
  }
  return errors;
}

function sourceExcerpt(source, lineNumber) {
  const lines = source.split(/\r?\n/);
  const start = Math.max(0, lineNumber - 2);
  const end = Math.min(lines.length, lineNumber + 1);
  return lines.slice(start, end).map((line, index) => {
    const number = start + index + 1;
    return `${number === lineNumber ? '>' : ' '} ${String(number).padStart(4)} | ${line}`;
  }).join('\n');
}

function validateInlineScripts(source, filePath) {
  const errors = [];
  const scriptPattern = /<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi;
  let match;
  let inlineIndex = 0;
  let checkedCount = 0;

  while ((match = scriptPattern.exec(source)) !== null) {
    const attributes = match[1];
    const code = match[2];
    if (attributeValue(attributes, 'src') !== null) continue;

    inlineIndex += 1;
    const type = (attributeValue(attributes, 'type') || '').toLowerCase();
    if (!JAVASCRIPT_TYPES.has(type) || !code.trim()) continue;
    checkedCount += 1;

    const contentStart = match.index + match[0].indexOf(code);
    const firstHtmlLine = source.slice(0, contentStart).split(/\r?\n/).length;
    const presets = type === 'text/babel' || type === 'text/jsx' ? ['react', 'env'] : ['env'];

    try {
      Babel.transform(code, {
        filename: `${path.basename(filePath)}#inline-${inlineIndex}`,
        presets,
        sourceType: 'unambiguous',
      });
    } catch (error) {
      const relativeLine = error.loc && Number.isInteger(error.loc.line) ? error.loc.line : 1;
      const htmlLine = firstHtmlLine + relativeLine - 1;
      const message = String(error.message || error).split(/\r?\n/, 1)[0];
      errors.push(`inline script ${inlineIndex} (${type || 'text/javascript'}), HTML line ${htmlLine}: ${message}\n${sourceExcerpt(source, htmlLine)}`);
    }
  }
  return { errors, checkedCount };
}

function validateFile(value) {
  const filePath = path.resolve(value);
  if (!fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    console.error(`ERROR ${filePath}: file not found`);
    return false;
  }

  let source;
  try {
    source = fs.readFileSync(filePath, 'utf8');
  } catch (error) {
    console.error(`ERROR ${path.basename(filePath)}: ${error.message}`);
    return false;
  }

  const errors = validateHtmlStructure(source);
  const inline = validateInlineScripts(source, filePath);
  errors.push(...inline.errors);
  if (errors.length) {
    for (const error of errors) console.error(`ERROR ${path.basename(filePath)}: ${error}`);
    return false;
  }

  console.log(`OK ${path.basename(filePath)}: HTML structure + ${inline.checkedCount} inline script(s)`);
  return true;
}

const args = process.argv.slice(2);
if (!args.length || args.includes('--help') || args.includes('-h')) {
  usage();
  process.exit(args.length ? 0 : 2);
}

const passed = args.map(validateFile).every(Boolean);
process.exit(passed ? 0 : 1);
