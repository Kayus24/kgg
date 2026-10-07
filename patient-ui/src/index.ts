export { KGG_PATIENT_UI_BUILD, mountPatientUiProbe } from "./mount"
export { PatientUiProbe } from "./PatientUiProbe"
export type { PatientUiProbeProps } from "./PatientUiProbe"

export {
  CLOSED_PATIENT_INPUT_SNAPSHOT,
  getWindowPatientInputController,
  isPatientInputController,
  usePatientInputSnapshot,
} from "./adapters/patientInputController"
export type {
  PatientInputController,
  PatientInputMeta,
  PatientInputSnapshot,
} from "./adapters/patientInputController"
