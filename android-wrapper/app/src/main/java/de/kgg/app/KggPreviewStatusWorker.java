package de.kgg.app;

import android.content.Context;

import androidx.annotation.NonNull;
import androidx.work.Worker;
import androidx.work.WorkerParameters;

public final class KggPreviewStatusWorker extends Worker {
    public KggPreviewStatusWorker(@NonNull Context context, @NonNull WorkerParameters parameters) {
        super(context, parameters);
    }

    @NonNull
    @Override
    public Result doWork() {
        if (BuildConfig.KGG_PREVIEW_STATUS_URL.trim().isEmpty()) {
            return Result.success();
        }
        try {
            KggPreviewStatus status = KggPreviewStatusClient.fetch();
            KggPreviewStatusNotifier.notifyIfChanged(getApplicationContext(), status);
            return Result.success();
        } catch (Exception ignored) {
            return Result.retry();
        }
    }
}
