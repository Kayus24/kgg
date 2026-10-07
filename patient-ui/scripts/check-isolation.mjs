import fs from "node:fs"
import path from "node:path"

const root = path.resolve(import.meta.dirname, "..")
const cssPath = path.join(root, "dist", "kgg-patient-ui.css")
const jsPath = path.join(root, "dist", "kgg-patient-ui.js")

for (const file of [cssPath, jsPath]) {
  if (!fs.existsSync(file)) {
    throw new Error(`missing build artifact: ${path.relative(root, file)}`)
  }
}

const css = fs.readFileSync(cssPath, "utf8")
const js = fs.readFileSync(jsPath, "utf8")

const forbiddenGlobalSelectors = [
  /(?:^|[},])\s*html\s*\{/,
  /(?:^|[},])\s*body\s*\{/,
  /(?:^|[},])\s*:root\s*\{/,
  /(?:^|[},])\s*button\s*\{/,
  /(?:^|[},])\s*input\s*\{/,
  /(?:^|[},])\s*textarea\s*\{/,
  /(?:^|[},])\s*select\s*\{/,
]

for (const pattern of forbiddenGlobalSelectors) {
  if (pattern.test(css)) {
    throw new Error(`unscoped legacy-risk CSS selector matched: ${pattern}`)
  }
}

if (!css.includes(".kgg-react-island")) {
  throw new Error("scoped KGG React island CSS marker is missing")
}

if (js.includes('getElementById("root")') || js.includes("getElementById('root')")) {
  throw new Error("library bundle contains an automatic dev-root mount")
}

const rawBytes = fs.statSync(jsPath).size
if (rawBytes > 1_000_000) {
  throw new Error(`patient UI bundle unexpectedly exceeds 1 MB: ${rawBytes} bytes`)
}

console.log(
  JSON.stringify({
    status: "PASS",
    cssScoped: true,
    automaticLiveMount: false,
    jsBytes: rawBytes,
  }),
)
