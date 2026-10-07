import path from "node:path"

import { chromium } from "playwright"
import { createServer } from "vite"

const root = path.resolve(import.meta.dirname, "..")
const port = 4174
const url = `http://127.0.0.1:${port}`

function assert(value, message) {
  if (!value) throw new Error(message)
}

async function waitSelected(page, kind, key) {
  await page.waitForFunction(
    ({ kind, key }) => {
      const button = document.querySelector(
        `[data-spike-kind="${kind}"] [data-key="${key}"]`,
      )
      if (!button) return false
      return (
        button.hasAttribute("data-pressed") ||
        button.hasAttribute("data-selected") ||
        button.getAttribute("aria-pressed") === "true"
      )
    },
    { kind, key },
    { timeout: 1500 },
  )
}

async function selectedKey(page, kind) {
  return page.evaluate((kind) => {
    const buttons = [
      ...document.querySelectorAll(
        `[data-spike-kind="${kind}"] [data-key]`,
      ),
    ]
    const selected = buttons.find(
      (button) =>
        button.hasAttribute("data-pressed") ||
        button.hasAttribute("data-selected") ||
        button.getAttribute("aria-pressed") === "true",
    )
    return selected?.getAttribute("data-key") ?? null
  }, kind)
}

async function activeKey(page) {
  return page.evaluate(
    () => document.activeElement?.getAttribute("data-key") ?? null,
  )
}

async function exercise(page, kind) {
  const a = page.locator(
    `[data-spike-kind="${kind}"] [data-key="a"]`,
  )
  const b = page.locator(
    `[data-spike-kind="${kind}"] [data-key="b"]`,
  )

  assert((await a.count()) === 1 && (await b.count()) === 1, `${kind}: buttons missing`)
  assert((await selectedKey(page, kind)) === "a", `${kind}: initial selection is not kg`)

  const aBox = await a.boundingBox()
  const bBox = await b.boundingBox()
  assert(aBox && bBox, `${kind}: button geometry missing`)
  assert(aBox.height >= 44 && bBox.height >= 44, `${kind}: touch target below 44px`)

  const scrollBefore = await page.evaluate(() => window.scrollY)
  await b.tap()
  await waitSelected(page, kind, "b")
  const scrollAfter = await page.evaluate(() => window.scrollY)
  assert(Math.abs(scrollAfter - scrollBefore) <= 1, `${kind}: tap changed page scroll`)
  const focusAfterTap = await activeKey(page)

  await a.focus()
  assert((await activeKey(page)) === "a", `${kind}: explicit focus did not reach kg`)
  await page.keyboard.press("ArrowRight")
  await page.waitForFunction(
    () => document.activeElement?.getAttribute("data-key") === "b",
    null,
    { timeout: 1000 },
  )

  return {
    kind,
    selectedAfterTap: await selectedKey(page, kind),
    focusAfterTap,
    arrowRightFocus: await activeKey(page),
    touchHeights: [aBox.height, bBox.height],
    scrollDelta: scrollAfter - scrollBefore,
  }
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
  const context = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 1,
    hasTouch: true,
    isMobile: true,
    locale: "de-DE",
  })
  const page = await context.newPage()
  const pageErrors = []
  page.on("pageerror", (error) => pageErrors.push(error.message))

  await page.goto(url, { waitUntil: "networkidle", timeout: 10_000 })
  await page.locator("[data-kgg-primitive-spike]").waitFor({
    state: "visible",
    timeout: 5_000,
  })

  const nativeTextInputs = await page.locator(
    "[data-kgg-primitive-spike] input, [data-kgg-primitive-spike] textarea",
  ).count()
  assert(nativeTextInputs === 0, "spike unexpectedly contains native text inputs")

  const base = await exercise(page, "base")
  const aria = await exercise(page, "aria")

  assert(pageErrors.length === 0, `page errors: ${JSON.stringify(pageErrors)}`)

  console.log(
    JSON.stringify({
      status: "PASS",
      viewport: "390x844",
      nativeTextInputs,
      pageErrors,
      results: [base, aria],
    }),
  )

  await context.close()
} finally {
  if (browser) await browser.close()
  await server.close()
}
