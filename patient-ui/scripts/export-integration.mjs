import fs from "node:fs"
import path from "node:path"

const packageRoot = path.resolve(import.meta.dirname, "..")
const repoRoot = path.resolve(packageRoot, "..")
const sourceDir = path.join(packageRoot, "dist")
const targetDir = path.join(repoRoot, "patient-react-dist")

const files = ["kgg-patient-ui.js", "kgg-patient-ui.css"]

fs.rmSync(targetDir, { recursive: true, force: true })
fs.mkdirSync(targetDir, { recursive: true })

for (const file of files) {
  const source = path.join(sourceDir, file)
  const target = path.join(targetDir, file)

  if (!fs.existsSync(source)) {
    throw new Error(`missing build artifact: ${file}`)
  }

  fs.copyFileSync(source, target)
}

console.log(
  JSON.stringify({
    status: "PASS",
    target: path.relative(repoRoot, targetDir),
    files,
  }),
)
