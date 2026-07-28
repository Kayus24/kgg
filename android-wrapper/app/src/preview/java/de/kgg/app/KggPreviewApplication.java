package de.kgg.app;

import android.app.Application;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.os.Build;
import android.util.Log;

import com.google.firebase.FirebaseApp;
import com.google.firebase.FirebaseOptions;
import com.google.firebase.messaging.FirebaseMessaging;

public final class KggPreviewApplication extends Application {
    static final String CHANNEL_ID = "kgg_preview_updates";
    static final String TOPIC = "kgg-preview";
    private static final String LOG_TAG = "KggPreviewPush";

    @Override
    public void onCreate() {
        super.onCreate();
        createNotificationChannel();
        initializeFirebase();
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) {
            return;
        }
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID,
                "KGG Test-Previews",
                NotificationManager.IMPORTANCE_HIGH
        );
        channel.setDescription("Meldet neue HTML-Previews fuer die KGG Test-App.");
        channel.enableVibration(true);
        NotificationManager manager = getSystemService(NotificationManager.class);
        if (manager != null) {
            manager.createNotificationChannel(channel);
        }
    }

    private void initializeFirebase() {
        if (!hasFirebaseConfiguration()) {
            Log.i(LOG_TAG, "Push is disabled because Preview Firebase configuration is absent.");
            return;
        }
        try {
            FirebaseOptions options = new FirebaseOptions.Builder()
                    .setProjectId(BuildConfig.KGG_FIREBASE_PROJECT_ID)
                    .setApplicationId(BuildConfig.KGG_FIREBASE_APPLICATION_ID)
                    .setApiKey(BuildConfig.KGG_FIREBASE_API_KEY)
                    .setGcmSenderId(BuildConfig.KGG_FIREBASE_SENDER_ID)
                    .build();
            FirebaseApp app = FirebaseApp.initializeApp(this, options);
            if (app == null) {
                Log.w(LOG_TAG, "Firebase initialization returned no app.");
                return;
            }
            FirebaseMessaging.getInstance()
                    .subscribeToTopic(TOPIC)
                    .addOnSuccessListener(unused -> Log.i(LOG_TAG, "Preview topic subscription is ready."))
                    .addOnFailureListener(error -> Log.w(LOG_TAG, "Topic subscription failed.", error));
        } catch (RuntimeException error) {
            Log.w(LOG_TAG, "Firebase initialization failed.", error);
        }
    }

    private boolean hasFirebaseConfiguration() {
        return !BuildConfig.KGG_FIREBASE_PROJECT_ID.trim().isEmpty()
                && !BuildConfig.KGG_FIREBASE_APPLICATION_ID.trim().isEmpty()
                && !BuildConfig.KGG_FIREBASE_API_KEY.trim().isEmpty()
                && !BuildConfig.KGG_FIREBASE_SENDER_ID.trim().isEmpty();
    }
}
