import { createRoot } from "react-dom/client"

import "./index.css"
import { getWindowPatientInputController } from "./adapters/patientInputController"
import { ControllerAdapterProbe } from "./dev/ControllerAdapterProbe"
import { SyntheticPatientInputController } from "./dev/SyntheticPatientInputController"

const target = document.getElementById("root")

if (!target) {
  throw new Error("KGG patient UI dev root is missing")
}

const controller = new SyntheticPatientInputController()

Object.assign(window, {
  __kggNumpadEditingApi: controller,
  __kggSyntheticPatientInputController: controller,
})

createRoot(target).render(
  <ControllerAdapterProbe controller={getWindowPatientInputController()} />,
)
