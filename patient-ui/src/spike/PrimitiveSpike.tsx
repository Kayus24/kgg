import { useState } from "react"
import { Toggle } from "@base-ui/react/toggle"
import { ToggleGroup } from "@base-ui/react/toggle-group"
import {
  ToggleButton,
  ToggleButtonGroup,
} from "react-aria-components/ToggleButtonGroup"

import "./primitive-spike.css"

type PairKey = "a" | "b"

function labelFor(value: PairKey) {
  return value === "a" ? "kg" : "Wdh"
}

function BaseUiPair() {
  const [value, setValue] = useState<PairKey>("a")

  return (
    <article className="kgg-spike-card" data-spike-kind="base">
      <p className="kgg-spike-label">Base UI</p>
      <ToggleGroup
        aria-label="Base UI Wertefeld"
        className="kgg-spike-group"
        value={[value]}
        onValueChange={(next) => {
          const candidate = next.at(-1)
          if (candidate === "a" || candidate === "b") setValue(candidate)
        }}
      >
        <Toggle className="kgg-spike-toggle" data-key="a" value="a">
          kg
        </Toggle>
        <Toggle className="kgg-spike-toggle" data-key="b" value="b">
          Wdh
        </Toggle>
      </ToggleGroup>
      <output className="kgg-spike-state" data-spike-state>
        aktiv: {labelFor(value)}
      </output>
    </article>
  )
}

function ReactAriaPair() {
  const [value, setValue] = useState<PairKey>("a")

  return (
    <article className="kgg-spike-card" data-spike-kind="aria">
      <p className="kgg-spike-label">React Aria</p>
      <ToggleButtonGroup
        aria-label="React Aria Wertefeld"
        className="kgg-spike-group"
        disallowEmptySelection
        selectedKeys={[value]}
        selectionMode="single"
        onSelectionChange={(keys) => {
          const candidate = [...keys][0]
          if (candidate === "a" || candidate === "b") setValue(candidate)
        }}
      >
        <ToggleButton className="kgg-spike-toggle" data-key="a" id="a">
          kg
        </ToggleButton>
        <ToggleButton className="kgg-spike-toggle" data-key="b" id="b">
          Wdh
        </ToggleButton>
      </ToggleButtonGroup>
      <output className="kgg-spike-state" data-spike-state>
        aktiv: {labelFor(value)}
      </output>
    </article>
  )
}

export function PrimitiveSpike() {
  return (
    <main className="kgg-react-island kgg-spike-shell" data-kgg-primitive-spike>
      <header className="kgg-spike-header">
        <p className="kgg-spike-eyebrow">P5 interaction spike</p>
        <h1>kg / Wdh primitive comparison</h1>
        <p>
          Isolated preview only. No patient plan, storage, QR, service worker, or
          live NumPad is connected.
        </p>
      </header>
      <section className="kgg-spike-grid">
        <BaseUiPair />
        <ReactAriaPair />
      </section>
    </main>
  )
}
