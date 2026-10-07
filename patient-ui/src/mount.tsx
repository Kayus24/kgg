import { createRoot, type Root } from "react-dom/client"

import { PatientUiProbe, type PatientUiProbeProps } from "./PatientUiProbe"
import "./index.css"

const roots = new WeakMap<Element, Root>()

export const KGG_PATIENT_UI_BUILD = "p4-react-island-skeleton-v1"

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
