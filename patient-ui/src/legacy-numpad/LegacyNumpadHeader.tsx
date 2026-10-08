import { useEffect, useState, useSyncExternalStore } from "react"
import { Toggle } from "@base-ui/react/toggle"
import { ToggleGroup } from "@base-ui/react/toggle-group"

import "./legacy-numpad-header.css"

type LegacyMeta = {
  ei?: number
  s?: number
  side?: string
  key?: string
}

type EditingSnapshot = {
  padOpen: boolean
  input: HTMLInputElement | null
  meta: LegacyMeta | null
  padValue: string
  dirty: boolean
}

type EditingApi = {
  getSnapshot?: () => EditingSnapshot
  subscribe?: (listener: () => void) => () => void
}

declare global {
  interface Window {
    __kggNumpadEditingApi?: EditingApi
  }
}

const CLOSED: EditingSnapshot = {
  padOpen: false,
  input: null,
  meta: null,
  padValue: "",
  dirty: false,
}

function getEditingSnapshot() {
  return window.__kggNumpadEditingApi?.getSnapshot?.() ?? CLOSED
}

function subscribeEditing(listener: () => void) {
  return window.__kggNumpadEditingApi?.subscribe?.(listener) ?? (() => undefined)
}

type PairItem = {
  key: string
  label: string
  value: string
  active: boolean
}

type TransferItem = {
  key: string
  label: string
  both: boolean
}

function readLegacyModel() {
  const pair = document.getElementById("kggPadPair")
  const transfer = document.getElementById("kggPadTransfer")

  const pairItems: PairItem[] = pair
    ? [...pair.querySelectorAll<HTMLButtonElement>(":scope > button[data-kgg-key]")].map(
        (button) => ({
          key: button.dataset.kggKey ?? "",
          label:
            button.querySelector<HTMLElement>(".kggPairLabel")?.textContent?.trim() ??
            "Wert",
          value:
            button.querySelector<HTMLElement>(".kggPairValue")?.textContent?.trim() ??
            "–",
          active: button.classList.contains("kggPairActive"),
        }),
      )
    : []

  const transferItems: TransferItem[] = transfer
    ? [
        ...transfer.querySelectorAll<HTMLButtonElement>(
          ":scope > button:not(.kggTransferGhost)",
        ),
      ].map((button) => ({
        key: button.dataset.kggTransferKey ?? "",
        label: button.textContent?.trim() ?? "",
        both: button.dataset.kggTransferBoth === "1",
      }))
    : []

  return { pairItems, transferItems }
}

function clickLegacyPair(key: string) {
  document
    .querySelector<HTMLButtonElement>(
      `#kggPadPair > button[data-kgg-key="${CSS.escape(key)}"]`,
    )
    ?.click()
}

function clickLegacyTransfer(item: TransferItem) {
  const selector = item.both
    ? "#kggPadTransfer > button[data-kgg-transfer-both='1']"
    : `#kggPadTransfer > button[data-kgg-transfer-key="${CSS.escape(item.key)}"]`

  document.querySelector<HTMLButtonElement>(selector)?.click()
}

function useLegacyRevision(padOpen: boolean) {
  const [, setRevision] = useState(0)

  useEffect(() => {
    const box = document.querySelector("#pad .padBox")
    if (!box) return

    let pairObserver: MutationObserver | null = null
    let transferObserver: MutationObserver | null = null

    const bump = () => setRevision((value) => value + 1)

    const attachLegacyObservers = () => {
      pairObserver?.disconnect()
      transferObserver?.disconnect()

      const pair = document.getElementById("kggPadPair")
      const transfer = document.getElementById("kggPadTransfer")

      if (pair) {
        pairObserver = new MutationObserver(bump)
        pairObserver.observe(pair, {
          attributes: true,
          childList: true,
          characterData: true,
          subtree: true,
        })
      }

      if (transfer) {
        transferObserver = new MutationObserver(bump)
        transferObserver.observe(transfer, {
          attributes: true,
          childList: true,
          characterData: true,
          subtree: true,
        })
      }
    }

    const boxObserver = new MutationObserver(() => {
      attachLegacyObservers()
      bump()
    })

    boxObserver.observe(box, { childList: true })
    attachLegacyObservers()
    bump()

    return () => {
      boxObserver.disconnect()
      pairObserver?.disconnect()
      transferObserver?.disconnect()
    }
  }, [padOpen])
}

export function LegacyNumpadHeader() {
  const editing = useSyncExternalStore(
    subscribeEditing,
    getEditingSnapshot,
    () => CLOSED,
  )
  useLegacyRevision(editing.padOpen)

  const model = readLegacyModel()

  if (!editing.padOpen || model.pairItems.length === 0) return null

  const activeKey =
    model.pairItems.find((item) => item.active)?.key ?? editing.meta?.key ?? ""

  return (
    <section
      className="kgg-react-numpad-header"
      data-kgg-react-numpad-header="v1"
      aria-label="Werteingabe"
    >
      <div className="kgg-react-numpad-header__tag" aria-hidden="true">
        Neu
      </div>

      <ToggleGroup
        aria-label="Aktives Wertefeld"
        className="kgg-react-numpad-pair"
        value={activeKey ? [activeKey] : []}
        onValueChange={(next) => {
          const candidate = next.at(-1)
          if (candidate && candidate !== activeKey) clickLegacyPair(candidate)
        }}
      >
        {model.pairItems.map((item) => (
          <Toggle
            className="kgg-react-numpad-pair__button"
            data-kgg-key={item.key}
            key={item.key}
            value={item.key}
          >
            <span className="kgg-react-numpad-pair__label">{item.label}</span>
            <span className="kgg-react-numpad-pair__value">{item.value}</span>
          </Toggle>
        ))}
      </ToggleGroup>

      {model.transferItems.length > 0 ? (
        <div
          className="kgg-react-numpad-transfer"
          data-count={model.transferItems.length}
        >
          {model.transferItems.map((item, index) => (
            <button
              className={
                item.both
                  ? "kgg-react-numpad-transfer__button kgg-react-numpad-transfer__button--both"
                  : "kgg-react-numpad-transfer__button"
              }
              data-kgg-transfer-both={item.both ? "1" : undefined}
              data-kgg-transfer-key={item.key || undefined}
              key={item.both ? "both" : `${item.key}-${index}`}
              onClick={() => clickLegacyTransfer(item)}
              type="button"
            >
              {item.label}
            </button>
          ))}
        </div>
      ) : null}
    </section>
  )
}
