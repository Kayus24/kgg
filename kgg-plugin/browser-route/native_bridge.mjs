export const NATIVE_HOST = "com.kgg.project_status_route";

export async function sendRouteObservation(chromeApi, observation) {
  try {
    const response = await chromeApi.runtime.sendNativeMessage(
      NATIVE_HOST,
      observation
    );
    if (!response || response.ok !== true) {
      return { ok: false, error: "native_host_rejected" };
    }
    return { ok: true };
  } catch {
    return { ok: false, error: "native_host_unavailable" };
  }
}
