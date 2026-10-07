import {
  CLOSED_PATIENT_INPUT_SNAPSHOT,
  type PatientInputController,
  type PatientInputMeta,
  type PatientInputSnapshot,
} from "../adapters/patientInputController"

export class SyntheticPatientInputController
  implements PatientInputController
{
  private listeners = new Set<() => void>()

  private snapshot: PatientInputSnapshot = CLOSED_PATIENT_INPUT_SNAPSHOT

  getSnapshot = () => this.snapshot

  subscribe = (listener: () => void) => {
    this.listeners.add(listener)
    return () => this.listeners.delete(listener)
  }

  openSynthetic(meta: PatientInputMeta, value = "0") {
    const input = document.createElement("input")
    input.value = value === "0" ? "" : value
    this.publish({
      padOpen: true,
      input,
      meta,
      padValue: value,
      dirty: false,
    })
  }

  typeSynthetic(value: string) {
    if (!this.snapshot.padOpen) return

    this.publish({
      ...this.snapshot,
      padValue: value,
      dirty: true,
    })
  }

  switchSynthetic(meta: PatientInputMeta, value = "0") {
    const input = document.createElement("input")
    input.value = value === "0" ? "" : value
    this.publish({
      padOpen: true,
      input,
      meta,
      padValue: value,
      dirty: false,
    })
  }

  closeSynthetic() {
    this.publish(CLOSED_PATIENT_INPUT_SNAPSHOT)
  }

  private publish(next: PatientInputSnapshot) {
    if (next === this.snapshot) return
    this.snapshot = next
    this.listeners.forEach((listener) => listener())
  }
}
