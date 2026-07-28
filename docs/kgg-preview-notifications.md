# KGG Preview notifications

The `de.kgg.preview` Android flavor can receive an immediate notification after
the guarded Preview channel publishes a new HTML build. Admin and colleague
flavors do not contain Firebase Messaging or the Android notification
permission.

## Delivery contract

1. `KGG GPT Preview Gate` completes in `publish_preview` mode.
2. `.github/workflows/kgg-preview-notify.yml` starts through `workflow_run`.
3. Trusted notifier code from the default branch verifies the source run,
   non-expired artifact, latest Preview index entry, `meta.json`, HTML response
   and SHA-256.
4. GitHub OIDC obtains a short-lived token restricted to Firebase Messaging.
5. FCM sends one high-priority message to topic `kgg-preview`.
6. Tapping the notification opens the Preview app, which downloads and verifies
   the current Preview through its existing updater.

A failed validation or notification never changes the published Preview and is
reported as `notification_delivery_failed`. `validate_only`, failed runs and
Admin-beta runs never send notifications.

## Required GitHub environment

Create a protected environment named `kgg-preview-notifications` with:

- variable `KGG_GCP_WIF_PROVIDER`
- variable `KGG_GCP_SERVICE_ACCOUNT`
- variable `KGG_FIREBASE_PROJECT_ID`

The Preview APK build also reads:

- variable `KGG_PREVIEW_FIREBASE_APPLICATION_ID`
- variable `KGG_PREVIEW_FIREBASE_SENDER_ID`
- secret `KGG_PREVIEW_FIREBASE_API_KEY`

No Firebase value is committed. A local build without these values remains
functional and simply leaves push disabled.

The Google Workload Identity provider must accept only this repository and the
default-branch `.github/workflows/kgg-preview-notify.yml` workflow. Its service
account needs only permission to send Firebase Cloud Messaging messages.

## Android behavior

- Topic: `kgg-preview`
- Channel: `kgg_preview_updates` (`KGG Test-Previews`)
- Importance: high, with sound and vibration
- Stable tag: `kgg-preview-latest`, so a new Preview replaces the old notice
- Android 13+: runtime notification permission requested only by the Preview app

After changing this integration, run:

```powershell
python release-pipeline\kgg_preview_notification.py --self-test
cmd /c release-pipeline\run-kgg-tests.cmd --suite android --level critical
cmd /c release-pipeline\run-kgg-tests.cmd --level critical
```
