import { useSyncExternalStore } from "react"

export type PatientInputMeta = {
  ei: number
  s: number
  side: string
  key: string
  label?: string
}

export type PatientInputSnapshot = {
  padOpen: boolean
  input: HTMLInputElement | null
  meta: PatientInputMeta | null
  padValue: string
  dirty: boolean
}

export type PatientInputController = {
  getSnapshot: () => PatientInputSnapshot
  subscribe: (listener: () => void) => () => void
  open?: () => boolean
  commitEditingInPlace?: () => boolean
  getEditingInput?: () => HTMLInputElement | null
  getEditingMeta?: () => PatientInputMeta | null
  getPadValue?: () => string
  isDirty?: () => boolean
  markDirty?: () => void
}

export const CLOSED_PATIENT_INPUT_SNAPSHOT: PatientInputSnapshot = Object.freeze({
  padOpen: false,
  input: null,
  meta: null,
  padValue: "",
  dirty: false,
})

export function isPatientInputController(
  value: unknown,
): value is PatientInputController {
  if (!value || typeof value !== "object") return false

  const candidate = value as Partial<PatientInputController>

  return (
    typeof candidate.getSnapshot === "function" &&
    typeof candidate.subscribe === "function"
  )
}

export function getWindowPatientInputController(
  host: Window = window,
): PatientInputController | null {
  const candidate = (
    host as Window & {
      __kggNumpadEditingApi?: unknown
    }
  ).__kggNumpadEditingApi

  return isPatientInputController(candidate) ? candidate : null
}

const subscribeClosed = () => () => undefined
const getClosedSnapshot = () => CLOSED_PATIENT_INPUT_SNAPSHOT

export function usePatientInputSnapshot(
  controller: PatientInputController | null,
): PatientInputSnapshot {
  return useSyncExternalStore(
    controller?.subscribe ?? subscribeClosed,
    controller?.getSnapshot ?? getClosedSnapshot,
    getClosedSnapshot,
  )
}
