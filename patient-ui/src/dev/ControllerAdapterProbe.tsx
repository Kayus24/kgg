import type { PatientInputController } from "../adapters/patientInputController"
import { usePatientInputSnapshot } from "../adapters/patientInputController"

export type ControllerAdapterProbeProps = {
  controller: PatientInputController | null
}

export function ControllerAdapterProbe({
  controller,
}: ControllerAdapterProbeProps) {
  const snapshot = usePatientInputSnapshot(controller)

  return (
    <section
      className="kgg-react-island kgg-react-probe"
      data-kgg-controller-probe
      data-pad-open={snapshot.padOpen ? "true" : "false"}
      data-dirty={snapshot.dirty ? "true" : "false"}
      data-key={snapshot.meta?.key ?? ""}
    >
      <p className="kgg-react-probe__eyebrow">P6 shadow adapter</p>
      <h1 className="kgg-react-probe__title">
        {snapshot.padOpen
          ? `aktiv: ${snapshot.meta?.key ?? "?"}`
          : "geschlossen"}
      </h1>
      <p className="kgg-react-probe__copy" data-kgg-controller-value>
        {snapshot.padOpen ? snapshot.padValue : "—"}
      </p>
    </section>
  )
}
