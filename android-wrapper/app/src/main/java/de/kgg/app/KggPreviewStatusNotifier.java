package de.kgg.app;

import android.Manifest;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.os.Build;

final class KggPreviewStatusNotifier {
    private static final String PREFS = "kgg_preview_status_prefs";
    private static final String PREF_LAST_EVENT = "last_notification_event";
    private static final String PROGRESS_CHANNEL = "kgg_preview_progress";
    private static final String RESULT_CHANNEL = "kgg_preview_result";
    private static final int PROGRESS_NOTIFICATION_ID = 7401;
    private static final int RESULT_NOTIFICATION_ID = 7402;

    private KggPreviewStatusNotifier() {
    }

    static boolean notifyIfChanged(Context context, KggPreviewStatus status) {
        if (status == null || !canNotify(context)) {
            return false;
        }
        SharedPreferences preferences = context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
        if (status.eventKey().equals(preferences.getString(PREF_LAST_EVENT, ""))) {
            return false;
        }
        NotificationManager manager = context.getSystemService(NotificationManager.class);
        if (manager == null) {
            return false;
        }
        ensureChannels(manager);
        if (status.isTerminal()) {
            manager.cancel(PROGRESS_NOTIFICATION_ID);
        }
        Intent intent = new Intent(context, MainActivity.class)
                .setFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        PendingIntent contentIntent = PendingIntent.getActivity(
                context,
                0,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        String channel = status.isTerminal() ? RESULT_CHANNEL : PROGRESS_CHANNEL;
        Notification.Builder builder = new Notification.Builder(context, channel)
                .setSmallIcon(android.R.drawable.stat_notify_sync)
                .setContentTitle(titleFor(status))
                .setContentText(status.requestId)
                .setStyle(new Notification.BigTextStyle().bigText(status.message + "\n" + status.requestId))
                .setContentIntent(contentIntent)
                .setAutoCancel(status.isTerminal())
                .setOngoing(!status.isTerminal())
                .setOnlyAlertOnce(!status.isTerminal());
        if (!status.isTerminal()) {
            builder.setProgress(0, 0, true);
        }
        manager.notify(status.isTerminal() ? RESULT_NOTIFICATION_ID : PROGRESS_NOTIFICATION_ID, builder.build());
        preferences.edit().putString(PREF_LAST_EVENT, status.eventKey()).apply();
        return true;
    }

    private static boolean canNotify(Context context) {
        return Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU
                || context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED;
    }

    private static String titleFor(KggPreviewStatus status) {
        if (status.phase.equals("validating")) {
            return "KGG Preview wird geprueft";
        }
        if (status.phase.equals("publishing")) {
            return "KGG Test-App wird aktualisiert";
        }
        if (status.phase.equals("success")) {
            return "Neue KGG Preview bereit";
        }
        return "KGG Preview fehlgeschlagen";
    }

    private static void ensureChannels(NotificationManager manager) {
        NotificationChannel progress = new NotificationChannel(
                PROGRESS_CHANNEL,
                "KGG Preview Status",
                NotificationManager.IMPORTANCE_LOW
        );
        progress.setDescription("Fortschritt der automatischen Test-App-Pipeline");
        NotificationChannel result = new NotificationChannel(
                RESULT_CHANNEL,
                "KGG Preview Ergebnisse",
                NotificationManager.IMPORTANCE_DEFAULT
        );
        result.setDescription("Neue oder fehlgeschlagene KGG Test-App-Previews");
        manager.createNotificationChannel(progress);
        manager.createNotificationChannel(result);
    }
}
