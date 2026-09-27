import { createRouteObserver } from "./route_observer.mjs";
import { sendRouteObservation } from "./native_bridge.mjs";

const observer = createRouteObserver(chrome, {
  emit: observation => sendRouteObservation(chrome, observation),
});

observer.start();
