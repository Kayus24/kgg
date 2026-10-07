import { createRoot } from "react-dom/client"

import "./index.css"
import { PrimitiveSpike } from "./spike/PrimitiveSpike"

const target = document.getElementById("root")

if (!target) {
  throw new Error("KGG patient UI dev root is missing")
}

createRoot(target).render(<PrimitiveSpike />)
