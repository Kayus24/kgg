import { createRoot, type Root } from "react-dom/client"

import { PatientUiProbe, type PatientUiProbeProps } from "./PatientUiProbe"
import { LegacyNumpadHeader } from "./legacy-numpad/LegacyNumpadHeader"
import { LegacyNumpadGrid } from "./legacy-numpad/LegacyNumpadGrid"
import "./index.css"

const roots = new WeakMap<Element, Root>()

export const KGG_PATIENT_UI_BUILD = "p8-d14-react-numpad-grid-optin-v1"

export function mountPatientUiProbe(
  target: Element,
  props: PatientUiProbeProps = {},
): () => void {
  let root = roots.get(target)

  if (!root) {
    root = createRoot(target)
    roots.set(target, root)
  }

  target.setAttribute("data-kgg-react-island", "probe")
  root.render(<PatientUiProbe {...props} />)

  return () => {
    const currentRoot = roots.get(target)
    if (!currentRoot) return

    currentRoot.unmount()
    roots.delete(target)
    target.removeAttribute("data-kgg-react-island")
  }
}

export function mountLegacyNumpadHeaderIsland(): (() => void) | null {
  const box = document.querySelector("#pad .padBox")
  if (!box) return null

  let target = document.getElementById("kggReactNumpadHeaderRoot")

  if (!target) {
    target = document.createElement("div")
    target.id = "kggReactNumpadHeaderRoot"
    box.appendChild(target)
  }

  let root = roots.get(target)
  if (!root) {
    root = createRoot(target)
    roots.set(target, root)
  }

  target.setAttribute("data-kgg-react-island", "numpad-header")
  document.body.classList.add("kggReactNumpadHeaderV1")
  root.render(<LegacyNumpadHeader />)

  return () => {
    const currentRoot = roots.get(target)
    currentRoot?.unmount()
    roots.delete(target)
    target.remove()
    document.body.classList.remove("kggReactNumpadHeaderV1")
  }
}

export function mountLegacyNumpadGridIsland(): (() => void) | null {
  const grid = document.querySelector<HTMLElement>("#pad .padGrid")
  if (!grid) return null

  const keys = [...grid.querySelectorAll<HTMLButtonElement>(":scope > button")]
  if (keys.length !== 12) return null

  let target = document.getElementById("kggReactNumpadGridRoot")
  if (!target) {
    target = document.createElement("div")
    target.id = "kggReactNumpadGridRoot"
    grid.appendChild(target)
  }

  const previousPosition = grid.style.position
  grid.style.position = "relative"

  let root = roots.get(target)
  if (!root) {
    root = createRoot(target)
    roots.set(target, root)
  }

  target.setAttribute("data-kgg-react-island", "numpad-grid")
  root.render(<LegacyNumpadGrid labels={keys.map((key) => key.textContent?.trim() ?? "")} />)

  return () => {
    roots.get(target)?.unmount()
    roots.delete(target)
    target.remove()
    grid.style.position = previousPosition
  }
}
