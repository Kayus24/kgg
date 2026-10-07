import { mountPatientUiProbe } from "./index"

const target = document.getElementById("root")

if (!target) {
  throw new Error("KGG patient UI dev root is missing")
}

mountPatientUiProbe(target, {
  label: "Preview only. This bundle is not wired into the live patient app.",
})
