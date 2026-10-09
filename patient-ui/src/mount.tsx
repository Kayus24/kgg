import { createRoot, type Root } from "react-dom/client"

import { PatientUiProbe, type PatientUiProbeProps } from "./PatientUiProbe"
import { LegacyNumpadHeader } from "./legacy-numpad/LegacyNumpadHeader"
import "./index.css"

const roots = new WeakMap<Element, Root>()

export const KGG_PATIENT_UI_BUILD = "p7-d14-react-numpad-header-v1"

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
