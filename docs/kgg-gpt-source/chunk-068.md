# KGG Source Chunk 068

- Source: `kgg-update/src` modular source
- Lines: 28561-28980

```html
        File directory = new File(getCacheDir(), "pdf");
        if (!directory.exists() && !directory.mkdirs()) {
            throw new IllegalStateException("pdf_cache_unavailable");
        }
        File file = new File(directory, safePdfFilename(filename));
        Files.write(file.toPath(), bytes);
        return file;
    }

    private boolean openPdfFile(File file) {
        try {
            Uri uri = FileProvider.getUriForFile(this, getPackageName() + ".fileprovider", file);
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(uri, "application/pdf");
            intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION);
            if (intent.resolveActivity(getPackageManager()) == null) {
                return openPdfFileInternally(file);
            }
            startActivity(intent);
            return true;
        } catch (ActivityNotFoundException err) {
            return openPdfFileInternally(file);
        } catch (Exception err) {
            boolean openedInternally = openPdfFileInternally(file);
            if (!openedInternally) {
                Toast.makeText(this, "PDF konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show();
            }
            return openedInternally;
        }
    }

    private boolean openPdfFileInternally(File file) {
        ArrayList<Bitmap> bitmaps = new ArrayList<>();
        try {
            if (file == null || !file.exists() || file.length() <= 0) {
                return false;
            }
            ParcelFileDescriptor descriptor = ParcelFileDescriptor.open(file, ParcelFileDescriptor.MODE_READ_ONLY);
            PdfRenderer renderer = new PdfRenderer(descriptor);
            int pageCount = renderer.getPageCount();
            int maxPages = Math.min(pageCount, 10);
            LinearLayout content = new LinearLayout(this);
            content.setOrientation(LinearLayout.VERTICAL);
            content.setPadding(24, 24, 24, 24);
            content.setBackgroundColor(Color.rgb(245, 248, 252));

            TextView title = new TextView(this);
            title.setText("KGG PDF-Vorschau");
            title.setTextColor(Color.rgb(7, 16, 39));
            title.setTextSize(20);
            title.setGravity(Gravity.CENTER_VERTICAL);
            title.setTypeface(android.graphics.Typeface.DEFAULT_BOLD);
            content.addView(title, new LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
            ));

            if (pageCount > maxPages) {
                TextView note = new TextView(this);
                note.setText("Vorschau zeigt die ersten " + maxPages + " von " + pageCount + " Seiten. Download/Druck bleiben vollstaendig.");
                note.setTextColor(Color.rgb(102, 112, 133));
                note.setTextSize(13);
                note.setPadding(0, 8, 0, 12);
                content.addView(note);
            }

            for (int index = 0; index < maxPages; index++) {
                PdfRenderer.Page page = renderer.openPage(index);
                int targetWidth = Math.min(1200, Math.max(720, getResources().getDisplayMetrics().widthPixels - 48));
                int targetHeight = Math.max(1, Math.round(targetWidth * (page.getHeight() / (float) page.getWidth())));
                Bitmap bitmap = Bitmap.createBitmap(targetWidth, targetHeight, Bitmap.Config.ARGB_8888);
                bitmap.eraseColor(Color.WHITE);
                page.render(bitmap, null, null, PdfRenderer.Page.RENDER_MODE_FOR_DISPLAY);
                page.close();
                bitmaps.add(bitmap);

                ImageView image = new ImageView(this);
                image.setAdjustViewBounds(true);
                image.setBackgroundColor(Color.WHITE);
                image.setImageBitmap(bitmap);
                LinearLayout.LayoutParams imageParams = new LinearLayout.LayoutParams(
                        LinearLayout.LayoutParams.MATCH_PARENT,
                        LinearLayout.LayoutParams.WRAP_CONTENT
                );
                imageParams.setMargins(0, 16, 0, 16);
                content.addView(image, imageParams);
            }
            renderer.close();
            descriptor.close();

            ScrollView scroll = new ScrollView(this);
            scroll.addView(content);

            Dialog dialog = new Dialog(this);
            dialog.setTitle("KGG PDF");
            dialog.setContentView(scroll);
            dialog.setOnDismissListener(ignored -> {
                for (Bitmap bitmap : bitmaps) {
                    if (bitmap != null && !bitmap.isRecycled()) {
                        bitmap.recycle();
                    }
                }
            });
            dialog.setOnShowListener(ignored -> {
                Window shown = dialog.getWindow();
                if (shown != null) {
                    shown.setLayout(WindowManager.LayoutParams.MATCH_PARENT, WindowManager.LayoutParams.MATCH_PARENT);
                }
            });
            dialog.show();
            Toast.makeText(this, "Interne PDF-Vorschau geoeffnet", Toast.LENGTH_SHORT).show();
            return true;
        } catch (Exception err) {
            for (Bitmap bitmap : bitmaps) {
                if (bitmap != null && !bitmap.isRecycled()) {
                    bitmap.recycle();
                }
            }
            return false;
        }
    }

    private Uri savePdfToDownloads(String filename, byte[] bytes) throws Exception {
        String safeName = safePdfFilename(filename);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, safeName);
            values.put(MediaStore.MediaColumns.MIME_TYPE, "application/pdf");
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                throw new IllegalStateException("downloads_insert_failed");
            }
            try (OutputStream output = getContentResolver().openOutputStream(uri)) {
                if (output == null) {
                    throw new IllegalStateException("downloads_stream_failed");
                }
                output.write(bytes);
            }
            values.clear();
            values.put(MediaStore.MediaColumns.IS_PENDING, 0);
            getContentResolver().update(uri, values, null, null);
            return uri;
        }
        File directory = getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
        if (directory == null) {
            directory = getFilesDir();
        }
        File pdfDirectory = new File(directory, "pdf");
        if (!pdfDirectory.exists() && !pdfDirectory.mkdirs()) {
            throw new IllegalStateException("documents_unavailable");
        }
        File file = new File(pdfDirectory, safeName);
        Files.write(file.toPath(), bytes);
        return Uri.fromFile(file);
    }

    private Uri saveTextToDownloads(String filename, String text, String mimeType) throws Exception {
        byte[] bytes = (text == null ? "" : text).getBytes(StandardCharsets.UTF_8);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            ContentValues values = new ContentValues();
            values.put(MediaStore.MediaColumns.DISPLAY_NAME, filename);
            values.put(MediaStore.MediaColumns.MIME_TYPE, mimeType == null ? "text/plain" : mimeType);
            values.put(MediaStore.MediaColumns.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
            values.put(MediaStore.MediaColumns.IS_PENDING, 1);
            Uri uri = getContentResolver().insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
            if (uri == null) {
                throw new IllegalStateException("downloads_insert_failed");
            }
            try (OutputStream output = getContentResolver().openOutputStream(uri)) {
                if (output == null) {
                    throw new IllegalStateException("downloads_stream_failed");
                }
                output.write(bytes);
            }
            values.clear();
            values.put(MediaStore.MediaColumns.IS_PENDING, 0);
            getContentResolver().update(uri, values, null, null);
            return uri;
        }
        File directory = getExternalFilesDir(Environment.DIRECTORY_DOCUMENTS);
        if (directory == null) {
            directory = getFilesDir();
        }
        File file = new File(directory, filename);
        Files.write(file.toPath(), bytes);
        return Uri.fromFile(file);
    }

    private String safeHtmlFilename(String filename) {
        String name = filename == null ? "" : filename.trim();
        if (name.isEmpty()) {
            name = "KGG_CURRENT_ADMIN_HTML.html";
        }
        name = name.replaceAll("[\\\\/:*?\"<>|]+", "_");
        if (!name.toLowerCase(Locale.ROOT).endsWith(".html")) {
            name += ".html";
        }
        return name;
    }

    private class KggPdfBridge {
        @JavascriptInterface
        public boolean openPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                File file = writePdfCacheFile(filename, bytes);
                runOnUiThread(() -> openPdfFile(file));
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF konnte nicht geoeffnet werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }

        @JavascriptInterface
        public boolean downloadPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                savePdfToDownloads(filename, bytes);
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF gespeichert", Toast.LENGTH_SHORT).show());
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "PDF konnte nicht gespeichert werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }

        @JavascriptInterface
        public boolean printPdfBase64(String filename, String base64) {
            try {
                byte[] bytes = decodePdfBase64(base64);
                String safeName = safePdfFilename(filename);
                runOnUiThread(() -> {
                    PrintManager printManager = (PrintManager) getSystemService(PRINT_SERVICE);
                    if (printManager != null) {
                        printManager.print("KGG " + safeName, new KggPdfPrintAdapter(safeName, bytes), new PrintAttributes.Builder().build());
                    }
                });
                return true;
            } catch (Exception err) {
                runOnUiThread(() -> Toast.makeText(MainActivity.this, "Drucken konnte nicht gestartet werden", Toast.LENGTH_SHORT).show());
                return false;
            }
        }
    }

    private static class KggPdfPrintAdapter extends PrintDocumentAdapter {
        private final String filename;
        private final byte[] bytes;

        KggPdfPrintAdapter(String filename, byte[] bytes) {
            this.filename = filename;
            this.bytes = bytes;
        }

        @Override
        public void onLayout(
                PrintAttributes oldAttributes,
                PrintAttributes newAttributes,
                CancellationSignal cancellationSignal,
                LayoutResultCallback callback,
                Bundle extras
        ) {
            if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                callback.onLayoutCancelled();
                return;
            }
            PrintDocumentInfo info = new PrintDocumentInfo.Builder(filename)
                    .setContentType(PrintDocumentInfo.CONTENT_TYPE_DOCUMENT)
                    .setPageCount(PrintDocumentInfo.PAGE_COUNT_UNKNOWN)
                    .build();
            callback.onLayoutFinished(info, true);
        }

        @Override
        public void onWrite(
                PageRange[] pages,
                ParcelFileDescriptor destination,
                CancellationSignal cancellationSignal,
                WriteResultCallback callback
        ) {
            if (cancellationSignal != null && cancellationSignal.isCanceled()) {
                callback.onWriteCancelled();
                return;
            }
            try (FileOutputStream output = new FileOutputStream(destination.getFileDescriptor())) {
                output.write(bytes);
                callback.onWriteFinished(new PageRange[]{PageRange.ALL_PAGES});
            } catch (Exception err) {
                callback.onWriteFailed(err.getMessage());
            }
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == RELEASE_HTML_REQUEST) {
            Uri selected = resultCode == RESULT_OK && data != null ? data.getData() : null;
            if (releaseController != null) {
                releaseController.onHtmlSelected(selected);
            }
            return;
        }
        if (requestCode == DOCUMENT_SCANNER_REQUEST) {
            if (filePathCallback == null) {
                pendingDocumentScannerParams = null;
                pendingDocumentScannerForceCamera = false;
                documentScannerFallbackStarted = false;
                return;
            }
            if (resultCode == RESULT_CANCELED) {
                completeFileChooserResult(null);
                return;
            }
            if (resultCode == RESULT_OK) {
                try {
                    GmsDocumentScanningResult scanResult =
                            GmsDocumentScanningResult.fromActivityResultIntent(data);
                    if (scanResult != null
                            && scanResult.getPages() != null
                            && !scanResult.getPages().isEmpty()
                            && scanResult.getPages().get(0).getImageUri() != null) {
                        completeFileChooserResult(new Uri[]{
                                scanResult.getPages().get(0).getImageUri()
                        });
                        return;
                    }
                } catch (Exception ignored) {
                }
                startLegacyScannerFallback();
                return;
            }
            completeFileChooserResult(null);
            return;
        }
        if (requestCode != FILE_CHOOSER_REQUEST || filePathCallback == null) {
            return;
        }
        Uri[] result = null;
        if (resultCode == RESULT_OK) {
            result = WebChromeClient.FileChooserParams.parseResult(resultCode, data);
            if ((result == null || result.length == 0) && cameraCaptureUri != null) {
                result = new Uri[]{cameraCaptureUri};
            }
        }
        completeFileChooserResult(result);
    }

    @Override
    public void onBackPressed() {
        handleAndroidBack();
    }

    private void handleAndroidBack() {
        if (webView == null) {
            MainActivity.super.onBackPressed();
            return;
        }
        webView.evaluateJavascript(
                "(function(){try{var m=document.getElementById('syncPairModal');"
                        + "if(m&&(m.classList.contains('open')||getComputedStyle(m).display!=='none')){m.classList.remove('open');return true;}"
                        + "return !!(window.KGGHandleAndroidBack&&window.KGGHandleAndroidBack());}catch(e){return false;}})();",
                value -> {
                    if ("true".equals(value)) {
                        return;
                    }
                    if (webView.canGoBack()) {
                        webView.goBack();
                        return;
                    }
                    MainActivity.super.onBackPressed();
                });
    }
}

<!-- SOURCE FILE: android-wrapper/app/src/main/assets/android/kgg_android_sync_bootstrap.js -->
(function(){
  function safeParse(text, fallback){
    try { return JSON.parse(text); } catch (err) { return fallback; }
  }

  if (!window.KGGNativeSync && window.KGGAndroidSync) {
    window.KGGNativeSync = {
      available: true,
      platform: 'android',
      status: function(){
        return safeParse(window.KGGAndroidSync.getStatus(), {available:true, platform:'android'});
      },
      read: function(){
        return safeParse(window.KGGAndroidSync.readSyncJson(), null);
      },
      write: function(syncDocument){
        return window.KGGAndroidSync.writeSyncJson(JSON.stringify(syncDocument || {}));
      },
      listPeers: function(){
        if (typeof window.KGGAndroidSync.listPeerSyncJson !== 'function') {
          return {kind:'kgg_cross_data_safe_sync_mesh', peers:[]};
        }
        return safeParse(window.KGGAndroidSync.listPeerSyncJson(), {kind:'kgg_cross_data_safe_sync_mesh', peers:[]});
      },
      getFollowConfig: function(){
        return safeParse(window.KGGAndroidSync.readFollowConfig(), {therapistId:'', syncRoomId:'', followedTherapists:[]});
      },
      setFollowConfig: function(config){
        return window.KGGAndroidSync.writeFollowConfig(JSON.stringify(config || {}));
      }
    };
  }

  if (!window.KGGNativeCamera && window.KGGAndroidApp) {
    window.KGGNativeCamera = {
      available: true,
      setNextPickerMode: function(mode){
        try {
          window.KGGAndroidApp.setNextFileChooserMode(mode === 'camera' ? 'camera' : 'file');
          return true;
        } catch (err) {
```
