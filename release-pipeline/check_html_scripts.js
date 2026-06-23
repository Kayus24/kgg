const fs = require("fs");
const vm = require("vm");

const files = process.argv.slice(2);
if (!files.length) {
  console.error("Usage: node check_html_scripts.js <html> [...]");
  process.exit(2);
}

let failures = 0;
for (const file of files) {
  const html = fs.readFileSync(file, "utf8");
  const scripts = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/gi)];
  scripts.forEach((match, index) => {
    const tag = match[0].slice(0, match[0].indexOf(">"));
    if (/type=["']application\/(?:ld\+)?json["']/i.test(tag) || /\ssrc=/i.test(tag)) return;
    try {
      new vm.Script(match[1], { filename: `${file}#script-${index}` });
    } catch (error) {
      failures += 1;
      console.error(error.stack || error.message);
    }
  });
}

if (failures) process.exit(1);
console.log(`HTML JavaScript syntax OK (${files.length} files)`);
