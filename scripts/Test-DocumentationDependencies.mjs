import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { test } from "node:test";
import katex from "katex";
import { micromark } from "micromark";
import { math, mathHtml } from "micromark-extension-math";
import MarkdownIt from "markdown-it";
import { load, YAML11_SCHEMA } from "js-yaml";
import { parse } from "smol-toml";

test("documentation parsers retain normal configuration and math behavior", () => {
  assert.deepEqual(load("default: true\nMD013: false\n"), { default: true, MD013: false });
  assert.deepEqual({ ...parse("default = true\nMD013 = false\n") }, { default: true, MD013: false });
  assert.match(new MarkdownIt().render("[guide](https://example.com)"), /href="https:\/\/example.com"/);
  const html = micromark("Inline $x^2$.\n\n$$\nx^2 + y^2\n$$\n", {
    extensions: [math()], htmlExtensions: [mathHtml()]
  });
  assert.match(html, /math-inline/);
  assert.match(html, /math-display/);
  assert.match(html, /class="katex"/);
});

test("KaTeX ignores inherited trust while preserving explicit trusted links", () => {
  const expression = String.raw`\href{javascript:alert(1)}{click}`;
  const inherited = Object.create({ trust: true });
  inherited.throwOnError = false;
  assert.doesNotMatch(katex.renderToString(expression, inherited), /href="javascript:/);
  Object.prototype.trust = true;
  try {
    assert.doesNotMatch(katex.renderToString(expression, { throwOnError: false }), /href="javascript:/);
  } finally {
    delete Object.prototype.trust;
  }
  assert.match(katex.renderToString(String.raw`\href{https://example.com}{guide}`, { trust: true }),
    /href="https:\/\/example.com"/);
});

test("RE2JS repeated lookbehind matching completes within a bounded worker", () => {
  // A separate process makes the deadline effective even if matching blocks its event loop.
  const result = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    import { RE2JS } from 're2js';
    for (const pattern of ['(?<=a)b', '(?<!b)a']) {
      const matcher = RE2JS.compile(pattern, RE2JS.LOOKBEHINDS).matcher('ab'.repeat(8000));
      let count = 0;
      while (matcher.find()) count++;
      assert.equal(count, pattern === '(?<=a)b' ? 8000 : 1);
    }
  `], { encoding: "utf8", timeout: 10000 });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
});

test("YAML empty merge sources consume the configured merge budget", () => {
  const source = 'arr: &arr [' + Array(100).fill('{}').join(',') + ']\n' +
    'targets:\n' + '  - <<: *arr\n'.repeat(100);
  assert.throws(() => load(source, { schema: YAML11_SCHEMA, maxTotalMergeKeys: 1000 }), /merge/i);
  assert.equal(load('base: &base {enabled: true}\nconfig: {<<: *base}\n',
    { schema: YAML11_SCHEMA }).config.enabled, true);
});

test("large TOML keys and incomplete Markdown references finish within a bounded worker", () => {
  const result = spawnSync(process.execPath, ["--input-type=module", "-e", `
    import assert from 'node:assert/strict';
    import { parse } from 'smol-toml';
    import MarkdownIt from 'markdown-it';
    const config = parse(Array.from({length: 256000}, (_, i) => 'k' + i + ' = 1').join('\\n'));
    assert.equal(Object.keys(config).length, 256000);
    const md = new MarkdownIt();
    assert.match(md.render('[a]: /u "' + 'x\\n'.repeat(200000)), /<p>/);
    assert.match(md.render('[' + 'a\\n'.repeat(20000)), /<p>/);
  `], { encoding: "utf8", timeout: 15000 });
  assert.equal(result.error, undefined, String(result.error));
  assert.equal(result.status, 0, result.stderr);
});
