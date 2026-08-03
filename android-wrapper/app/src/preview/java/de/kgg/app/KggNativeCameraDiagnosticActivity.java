package de.kgg.app;

import android.Manifest;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.graphics.Color;
import android.hardware.camera2.CameraCharacteristics;
import android.hardware.camera2.CameraManager;
import android.os.Build;
import android.os.Bundle;
import android.provider.MediaStore;
import android.util.Range;
import android.util.SizeF;
import android.view.Gravity;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.ComponentActivity;
import androidx.annotation.OptIn;
import androidx.camera.camera2.interop.Camera2CameraInfo;
import androidx.camera.camera2.interop.ExperimentalCamera2Interop;
import androidx.camera.core.Camera;
import androidx.camera.core.CameraInfo;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.Preview;
import androidx.camera.core.ZoomState;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import com.google.common.util.concurrent.ListenableFuture;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Set;

@OptIn(markerClass = ExperimentalCamera2Interop.class)
public final class KggNativeCameraDiagnosticActivity extends ComponentActivity {
    private static final int CAMERA_PERMISSION_REQUEST = 7301;

    private final List<Candidate> candidates = new ArrayList<>();
    private PreviewView previewView;
    private TextView statusView;
    private TextView counterView;
    private TextView detailsView;
    private ProcessCameraProvider cameraProvider;
    private Camera activeCamera;
    private int selectedIndex;

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        setContentView(createUi());
        if (hasCameraPermission()) {
            loadCameraProvider();
        } else {
            ActivityCompat.requestPermissions(
                    this,
                    new String[]{Manifest.permission.CAMERA},
                    CAMERA_PERMISSION_REQUEST
            );
        }
    }

    private LinearLayout createUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(dp(10), dp(8), dp(10), dp(10));
        root.setBackgroundColor(Color.rgb(2, 6, 23));

        LinearLayout header = new LinearLayout(this);
        header.setGravity(Gravity.CENTER_VERTICAL);
        TextView title = text("Native Kamera-Diagnose", 20, Color.WHITE, true);
        header.addView(title, new LinearLayout.LayoutParams(0, -2, 1));
        Button close = button("Schließen");
        close.setOnClickListener(view -> finish());
        header.addView(close);
        root.addView(header);

        root.addView(text(
                "Preview-only. Keine Bilder, QR-Inhalte, Patientendaten oder vollständigen Kamera-IDs werden gespeichert.",
                13,
                Color.rgb(203, 213, 225),
                false
        ));

        previewView = new PreviewView(this);
        previewView.setScaleType(PreviewView.ScaleType.FIT_CENTER);
        previewView.setImplementationMode(PreviewView.ImplementationMode.COMPATIBLE);
        previewView.setBackgroundColor(Color.BLACK);
        root.addView(previewView, new LinearLayout.LayoutParams(-1, 0, 1));

        statusView = text("Kamera wird vorbereitet …", 14, Color.WHITE, true);
        statusView.setPadding(dp(8), dp(8), dp(8), dp(8));
        root.addView(statusView);
        counterView = text("Kamera –", 14, Color.rgb(219, 234, 254), true);
        root.addView(counterView);

        ScrollView scroll = new ScrollView(this);
        detailsView = text("Noch keine nativen Kameradaten.", 13, Color.rgb(226, 232, 240), false);
        detailsView.setTextIsSelectable(true);
        detailsView.setPadding(dp(8), dp(8), dp(8), dp(8));
        detailsView.setBackgroundColor(Color.rgb(15, 23, 42));
        scroll.addView(detailsView);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, dp(165)));

        LinearLayout controls = new LinearLayout(this);
        addButton(controls, "Vorherige", view -> select(-1));
        addButton(controls, "Zoom minimum", view -> setMinimumZoom());
        addButton(controls, "Nächste", view -> select(1));
        root.addView(controls);

        LinearLayout actions = new LinearLayout(this);
        addButton(actions, "Systemkamera 1×", view -> openSystemCamera());
        addButton(actions, "Bericht kopieren", view -> copyReport());
        root.addView(actions);
        return root;
    }

    private void addButton(LinearLayout row, String label, android.view.View.OnClickListener listener) {
        Button button = button(label);
        button.setOnClickListener(listener);
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(0, dp(48), 1);
        params.setMargins(dp(3), dp(3), dp(3), dp(3));
        row.addView(button, params);
    }

    private TextView text(String value, int size, int color, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextSize(size);
        view.setTextColor(color);
        if (bold) view.setTypeface(view.getTypeface(), android.graphics.Typeface.BOLD);
        return view;
    }

    private Button button(String value) {
        Button button = new Button(this);
        button.setText(value);
        button.setAllCaps(false);
        return button;
    }

    private boolean hasCameraPermission() {
        return ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                == PackageManager.PERMISSION_GRANTED;
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] permissions, int[] results) {
        super.onRequestPermissionsResult(code, permissions, results);
        if (code != CAMERA_PERMISSION_REQUEST) return;
        if (results.length > 0 && results[0] == PackageManager.PERMISSION_GRANTED) {
            loadCameraProvider();
        } else {
            setStatus("Kamera-Berechtigung fehlt.", true);
        }
    }

    private void loadCameraProvider() {
        setStatus("Native Kameras werden ermittelt …", false);
        ListenableFuture<ProcessCameraProvider> future = ProcessCameraProvider.getInstance(this);
        future.addListener(() -> {
            try {
                cameraProvider = future.get();
                enumerateCandidates();
                if (candidates.isEmpty()) {
                    setStatus("CameraX meldet keine Kamera.", true);
                    renderDetails();
                } else {
                    bindSelected();
                }
            } catch (Exception error) {
                setStatus("CameraX-Fehler: " + error.getClass().getSimpleName(), true);
            }
        }, ContextCompat.getMainExecutor(this));
    }

    private void enumerateCandidates() {
        candidates.clear();
        Map<String, Candidate> unique = new LinkedHashMap<>();
        CameraManager manager = (CameraManager) getSystemService(Context.CAMERA_SERVICE);
        for (CameraInfo logicalInfo : cameraProvider.getAvailableCameraInfos()) {
            try {
                String logicalId = Camera2CameraInfo.from(logicalInfo).getCameraId();
                CameraCharacteristics logicalChars = manager.getCameraCharacteristics(logicalId);
                boolean rear = Integer.valueOf(CameraCharacteristics.LENS_FACING_BACK)
                        .equals(logicalChars.get(CameraCharacteristics.LENS_FACING));
                Set<CameraInfo> physicalInfos = logicalInfo.getPhysicalCameraInfos();
                int physicalCount = physicalInfos == null ? 0 : physicalInfos.size();
                putCandidate(unique, Candidate.create(
                        logicalId, null, logicalInfo, logicalChars, rear, physicalCount
                ));
                if (physicalInfos != null) {
                    for (CameraInfo physicalInfo : physicalInfos) {
                        try {
                            String physicalId = Camera2CameraInfo.from(physicalInfo).getCameraId();
                            putCandidate(unique, Candidate.create(
                                    logicalId,
                                    physicalId,
                                    physicalInfo,
                                    manager.getCameraCharacteristics(physicalId),
                                    rear,
                                    physicalCount
                            ));
                        } catch (Exception ignored) {
                        }
                    }
                }
            } catch (Exception ignored) {
            }
        }
        for (Candidate candidate : unique.values()) {
            if (candidate.rear) candidates.add(candidate);
        }
        if (candidates.isEmpty()) candidates.addAll(unique.values());
        candidates.sort((left, right) -> Double.compare(right.fieldOfView, left.fieldOfView));
    }

    private void putCandidate(Map<String, Candidate> target, Candidate candidate) {
        target.put(candidate.logicalId + "|" + candidate.physicalId, candidate);
    }

    private void select(int direction) {
        if (candidates.isEmpty()) return;
        selectedIndex = (selectedIndex + direction + candidates.size()) % candidates.size();
        bindSelected();
    }

    private void bindSelected() {
        Candidate candidate = candidates.get(selectedIndex);
        try {
            cameraProvider.unbindAll();
            CameraSelector.Builder builder = new CameraSelector.Builder().addCameraFilter(infos -> {
                List<CameraInfo> matching = new ArrayList<>();
                for (CameraInfo info : infos) {
                    try {
                        if (candidate.logicalId.equals(Camera2CameraInfo.from(info).getCameraId())) {
                            matching.add(info);
                        }
                    } catch (Exception ignored) {
                    }
                }
                return matching;
            });
            if (candidate.physicalId != null) builder.setPhysicalCameraId(candidate.physicalId);
            Preview preview = new Preview.Builder().build();
            preview.setSurfaceProvider(previewView.getSurfaceProvider());
            activeCamera = cameraProvider.bindToLifecycle(this, builder.build(), preview);
            activeCamera.getCameraControl().setLinearZoom(0f);
            setStatus("Kamera aktiv. Sichtfeld vergleichen.", false);
        } catch (Exception error) {
            activeCamera = null;
            setStatus("Kamera konnte nicht geöffnet werden: " + error.getClass().getSimpleName(), true);
        }
        renderDetails();
    }

    private void setMinimumZoom() {
        if (activeCamera == null) {
            setStatus("Keine aktive Kamera.", true);
            return;
        }
        activeCamera.getCameraControl().setLinearZoom(0f);
        setStatus("Minimaler Zoom angefordert.", false);
        previewView.postDelayed(this::renderDetails, 250);
    }

    private void renderDetails() {
        if (candidates.isEmpty()) {
            counterView.setText("Kameras: 0");
            detailsView.setText("Keine native Kamera verfügbar.");
            return;
        }
        Candidate candidate = candidates.get(selectedIndex);
        ZoomState zoom = activeCamera == null ? null
                : activeCamera.getCameraInfo().getZoomState().getValue();
        counterView.setText("Kamera " + (selectedIndex + 1) + " von " + candidates.size());
        detailsView.setText(candidate.describe(zoom));
    }

    private void copyReport() {
        ClipboardManager clipboard = (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
        if (clipboard == null) return;
        StringBuilder report = new StringBuilder("KGG Native Kamera-Diagnose v2\n")
                .append("Kameras: ").append(candidates.size()).append('\n')
                .append("Preview: FIT_CENTER\n")
                .append("Bilder gespeichert: nein\n")
                .append("Vollständige Kamera-IDs: nein\n");
        for (int i = 0; i < candidates.size(); i++) {
            report.append("\nKamera ").append(i + 1).append('\n')
                    .append(candidates.get(i).describe(null)).append('\n');
        }
        report.append("\nVisuell weiteste Kamera: Kamera ___\n")
                .append("Systemkamera 1× deutlich weiter: ja / nein\n");
        clipboard.setPrimaryClip(ClipData.newPlainText("KGG Kamera-Diagnose", report.toString()));
        Toast.makeText(this, "Diagnosebericht kopiert", Toast.LENGTH_SHORT).show();
    }

    private void openSystemCamera() {
        Intent intent = new Intent(MediaStore.INTENT_ACTION_STILL_IMAGE_CAMERA);
        if (intent.resolveActivity(getPackageManager()) == null) {
            Toast.makeText(this, "Systemkamera nicht verfügbar", Toast.LENGTH_SHORT).show();
            return;
        }
        startActivity(intent);
    }

    private void setStatus(String value, boolean warning) {
        statusView.setText(value);
        statusView.setBackgroundColor(warning ? Color.rgb(120, 53, 15) : Color.rgb(30, 41, 59));
    }

    @Override
    protected void onStart() {
        super.onStart();
        if (cameraProvider != null && !candidates.isEmpty() && activeCamera == null && hasCameraPermission()) {
            bindSelected();
        }
    }

    @Override
    protected void onStop() {
        if (cameraProvider != null) cameraProvider.unbindAll();
        activeCamera = null;
        super.onStop();
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    private static String number(double value) {
        return !Double.isFinite(value) || value <= 0
                ? "nicht gemeldet"
                : String.format(Locale.GERMANY, "%.2f", value);
    }

    private static final class Candidate {
        final String logicalId;
        final String physicalId;
        final String safeId;
        final boolean rear;
        final float intrinsicZoom;
        final float minimumZoom;
        final float maximumZoom;
        final float maximumDigitalZoom;
        final String focalLengths;
        final String sensorSize;
        final double fieldOfView;
        final int physicalCount;

        Candidate(String logicalId, String physicalId, String safeId, boolean rear,
                  float intrinsicZoom, float minimumZoom, float maximumZoom,
                  float maximumDigitalZoom, String focalLengths, String sensorSize,
                  double fieldOfView, int physicalCount) {
            this.logicalId = logicalId;
            this.physicalId = physicalId;
            this.safeId = safeId;
            this.rear = rear;
            this.intrinsicZoom = intrinsicZoom;
            this.minimumZoom = minimumZoom;
            this.maximumZoom = maximumZoom;
            this.maximumDigitalZoom = maximumDigitalZoom;
            this.focalLengths = focalLengths;
            this.sensorSize = sensorSize;
            this.fieldOfView = fieldOfView;
            this.physicalCount = physicalCount;
        }

        static Candidate create(String logicalId, String physicalId, CameraInfo info,
                                CameraCharacteristics chars, boolean rear, int physicalCount) {
            float intrinsic = 1f;
            try { intrinsic = info.getIntrinsicZoomRatio(); } catch (Exception ignored) {}
            float minimum = 1f;
            float maximum = 1f;
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                Range<Float> range = chars.get(CameraCharacteristics.CONTROL_ZOOM_RATIO_RANGE);
                if (range != null) {
                    minimum = range.getLower();
                    maximum = range.getUpper();
                }
            }
            Float digital = chars.get(CameraCharacteristics.SCALER_AVAILABLE_MAX_DIGITAL_ZOOM);
            float[] focals = chars.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS);
            SizeF sensor = chars.get(CameraCharacteristics.SENSOR_INFO_PHYSICAL_SIZE);
            double fov = 0;
            if (sensor != null && focals != null && focals.length > 0) {
                float shortest = focals[0];
                for (float focal : focals) if (focal > 0 && focal < shortest) shortest = focal;
                if (shortest > 0) fov = Math.toDegrees(2 * Math.atan(sensor.getWidth() / (2 * shortest)));
            }
            String rawId = logicalId + "|" + (physicalId == null ? "logical" : physicalId);
            return new Candidate(
                    logicalId,
                    physicalId,
                    hash(rawId),
                    rear,
                    intrinsic,
                    minimum,
                    maximum,
                    digital == null ? 1f : digital,
                    focals == null || focals.length == 0 ? "nicht gemeldet" : Arrays.toString(focals),
                    sensor == null ? "nicht gemeldet" : String.format(
                            Locale.GERMANY, "%.2f × %.2f", sensor.getWidth(), sensor.getHeight()
                    ),
                    fov,
                    physicalCount
            );
        }

        String describe(ZoomState zoom) {
            return "Kennung: Kamera-" + safeId + "\n"
                    + "Rückkamera: " + rear + "\n"
                    + "Auswahl: " + (physicalId == null ? "logisch / automatisch" : "physische Linse") + "\n"
                    + "Physische Linse fest: " + (physicalId != null) + "\n"
                    + "Intrinsic Zoom: " + number(intrinsicZoom) + "\n"
                    + "Zoom min/max: " + number(minimumZoom) + " / " + number(maximumZoom) + "\n"
                    + "Zoom aktuell: " + (zoom == null ? "nicht gemeldet" : number(zoom.getZoomRatio())) + "\n"
                    + "Max. digitaler Zoom: " + number(maximumDigitalZoom) + "\n"
                    + "Brennweiten mm: " + focalLengths + "\n"
                    + "Sensor mm: " + sensorSize + "\n"
                    + "Sichtfeld geschätzt: " + (fieldOfView > 0 ? number(fieldOfView) + "°" : "nicht berechenbar") + "\n"
                    + "Physische Kameras: " + physicalCount + "\n"
                    + "Preview: FIT_CENTER";
        }

        private static String hash(String value) {
            try {
                byte[] bytes = MessageDigest.getInstance("SHA-256")
                        .digest(value.getBytes(StandardCharsets.UTF_8));
                return String.format(Locale.ROOT, "%02x%02x%02x%02x",
                        bytes[0], bytes[1], bytes[2], bytes[3]);
            } catch (Exception ignored) {
                return "redacted";
            }
        }
    }
}
