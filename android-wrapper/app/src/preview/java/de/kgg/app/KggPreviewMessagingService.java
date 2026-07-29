package de.kgg.app;

import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Intent;
import android.util.Log;

import androidx.core.app.NotificationCompat;

import com.google.firebase.messaging.FirebaseMessagingService;
import com.google.firebase.messaging.RemoteMessage;

public final class KggPreviewMessagingService extends FirebaseMessagingService {
    private static final int NOTIFICATION_ID = 6101;
    private static final String NOTIFICATION_TAG = "kgg-preview-latest";
    private static final String LOG_TAG = "KggPreviewPush";

    @Override
    public void onNewToken(String token) {
        Log.i(LOG_TAG, "FCM token refreshed.");
    }

    @Override
    public void onMessageReceived(RemoteMessage message) {
        String title = "Neue KGG Preview";
        String body = clean(message.getData().get("title"), "Eine neue Testversion ist bereit.");
        RemoteMessage.Notification notification = message.getNotification();
        if (notification != null) {
            title = clean(notification.getTitle(), title);
            body = clean(notification.getBody(), body);
        }

        Intent intent = new Intent(this, MainActivity.class)
                .setAction("de.kgg.preview.OPEN_LATEST")
                .addFlags(Intent.FLAG_ACTIVITY_CLEAR_TOP | Intent.FLAG_ACTIVITY_SINGLE_TOP);
        copyExtra(message, intent, "request_id");
        copyExtra(message, intent, "rollout_code");
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this,
                0,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        NotificationCompat.Builder builder = new NotificationCompat.Builder(
                this,
                KggPreviewApplication.CHANNEL_ID
        )
                .setSmallIcon(R.drawable.ic_kgg_preview_notification)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new NotificationCompat.BigTextStyle().bigText(body))
                .setPriority(NotificationCompat.PRIORITY_HIGH)
                .setAutoCancel(true)
                .setContentIntent(pendingIntent);
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.notify(NOTIFICATION_TAG, NOTIFICATION_ID, builder.build());
        }
    }

    private static void copyExtra(RemoteMessage message, Intent intent, String key) {
        String value = message.getData().get(key);
        if (value != null && !value.trim().isEmpty()) {
            intent.putExtra(key, value);
        }
    }

    private static String clean(String value, String fallback) {
        return value == null || value.trim().isEmpty() ? fallback : value.trim();
    }
}
