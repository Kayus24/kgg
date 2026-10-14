import { useLayoutEffect } from "react"

import "./legacy-numpad-grid.css"

// P8 owns the presentation only. The existing 12 legacy keys own all actions.
const LEGACY_KEYS = "#pad .padGrid > button"
const KEY_COUNT = 12

function delegateLegacyKey(index: number) {
  const keys = document.querySelectorAll<HTMLButtonElement>(LEGACY_KEYS)
  if (keys.length !== KEY_COUNT || index < 0 || index >= KEY_COUNT) return
  const key = keys.item(index)
  if (key && !key.disabled) key.click()
}

export function LegacyNumpadGrid({ labels }: { labels: readonly string[] }) {
  useLayoutEffect(() => {
    const keys = [...document.querySelectorAll<HTMLButtonElement>(LEGACY_KEYS)]
    if (keys.length !== KEY_COUNT) return
    const old = keys.map((key) => ({
      visibility: key.style.visibility,
      pointerEvents: key.style.pointerEvents,
      ariaHidden: key.getAttribute("aria-hidden"),
      tabIndex: key.getAttribute("tabindex"),
    }))
    keys.forEach((key) => {
      key.style.visibility = "hidden"
      key.style.pointerEvents = "none"
      key.setAttribute("aria-hidden", "true")
      key.tabIndex = -1
    })
    document.body.classList.add("kggReactNumpadGridV1")
    return () => {
      document.body.classList.remove("kggReactNumpadGridV1")
      keys.forEach((key, index) => {
        const previous = old[index]
        key.style.visibility = previous.visibility
        key.style.pointerEvents = previous.pointerEvents
        if (previous.ariaHidden === null) key.removeAttribute("aria-hidden")
        else key.setAttribute("aria-hidden", previous.ariaHidden)
        if (previous.tabIndex === null) key.removeAttribute("tabindex")
        else key.setAttribute("tabindex", previous.tabIndex)
      })
    }
  }, [])

  if (labels.length !== KEY_COUNT) return null

  return (
    <div className="kgg-react-numpad-grid" role="group"
      aria-label="Zifferntastatur" data-kgg-react-numpad-grid="v1">
      {labels.map((label, index) => (
        <button key={index} type="button"
          className="kgg-react-numpad-grid__key"
          data-kgg-legacy-key-index={index}
          onClick={() => delegateLegacyKey(index)}>{label}</button>
      ))}
    </div>
  )
}
