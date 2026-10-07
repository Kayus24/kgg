import path from "node:path"

import { chromium } from "playwright"
import { createServer } from "vite"

const root = path.resolve(import.meta.dirname, "..")
const port = 4175
const url = `http://127.0.0.1:${port}`

function assert(value, message) {
  if (!value) throw new Error(message)
}

async function readProbe(page) {
  return page.locator("[data-kgg-controller-probe]").evaluate((node) => ({
    padOpen: node.getAttribute("data-pad-open"),
    dirty: node.getAttribute("data-dirty"),
    key: node.getAttribute("data-key"),
    value:
      node.querySelector("[data-kgg-controller-value]")?.textContent?.trim() ??
      "",
  }))
}

async function waitProbe(page, expected) {
  await page.waitForFunction(
    (next) => {
      const node = document.querySelector("[data-kgg-controller-probe]")
      if (!node) return false

      const current = {
        padOpen: node.getAttribute("data-pad-open"),
        dirty: node.getAttribute("data-dirty"),
        key: node.getAttribute("data-key"),
        value:
          node
            .querySelector("[data-kgg-controller-value]")
            ?.textContent?.trim() ?? "",
      }

      return Object.entries(next).every(
        ([key, value]) => current[key] === value,
      )
    },
    expected,
    { timeout: 1500 },
  )
}

const server = await createServer({
  root,
  logLevel: "error",
  server: {
    host: "127.0.0.1",
    port,
    strictPort: true,
  },
})

let browser

try {
  await server.listen()
  browser = await chromium.launch({ headless: true })

  const page = await browser.newPage({
    viewport: { width: 390, height: 844 },
  })
  const pageErrors = []
  page.on("pageerror", (error) => pageErrors.push(error.message))

  await page.goto(url, { waitUntil: "networkidle", timeout: 10_000 })
  await page.locator("[data-kgg-controller-probe]").waitFor({
    state: "visible",
    timeout: 5_000,
  })

  const initial = await readProbe(page)
  assert(
    JSON.stringify(initial) ===
      JSON.stringify({
        padOpen: "false",
        dirty: "false",
        key: "",
        value: "—",
      }),
    `initial closed snapshot mismatch: ${JSON.stringify(initial)}`,
  )

  await page.evaluate(() => {
    window.__kggSyntheticPatientInputController.openSynthetic(
      { ei: 0, s: 1, side: "B", key: "a", label: "kg" },
      "0",
    )
  })
  await waitProbe(page, {
    padOpen: "true",
    dirty: "false",
    key: "a",
    value: "0",
  })

  await page.evaluate(() => {
    window.__kggSyntheticPatientInputController.typeSynthetic("7")
  })
  await waitProbe(page, {
    padOpen: "true",
    dirty: "true",
    key: "a",
    value: "7",
  })

  await page.evaluate(() => {
    window.__kggSyntheticPatientInputController.switchSynthetic(
      { ei: 0, s: 1, side: "B", key: "b", label: "Wdh" },
      "0",
    )
  })
  await waitProbe(page, {
    padOpen: "true",
    dirty: "false",
    key: "b",
    value: "0",
  })

  await page.evaluate(() => {
    window.__kggSyntheticPatientInputController.closeSynthetic()
  })
  await waitProbe(page, {
    padOpen: "false",
    dirty: "false",
    key: "",
    value: "—",
  })

  assert(pageErrors.length === 0, `page errors: ${JSON.stringify(pageErrors)}`)

  console.log(
    JSON.stringify({
      status: "PASS",
      globalControllerResolved: true,
      transitions: ["closed", "open-a", "dirty-a", "switch-b", "closed"],
      pageErrors,
    }),
  )
} finally {
  if (browser) await browser.close()
  await server.close()
}
