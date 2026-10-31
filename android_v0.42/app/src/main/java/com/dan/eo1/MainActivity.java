package com.dan.eo1;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.text.InputType;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import android.os.StatFs;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;
import java.util.Properties;

public class MainActivity extends Activity {

    // ------------------------------------------------------------
    // Basic settings
    // ------------------------------------------------------------

    private static final String MEDIA_DIR =
            "/sdcard/EO1-Museum/images";

    private static final String ART_DIR =
            "/sdcard/EO1-Museum/art";

    private static final String LOG_FILE =
            "/sdcard/EO1-Museum/mouse_log.txt";

    private static final String CONFIG_FILE =
            "/sdcard/EO1-Museum/.config";

    private static final String DEFAULT_NETWORK_HOST =
            "192.168.1.103";

    private static final int DEFAULT_NETWORK_PORT = 8000;

    private static final int DEFAULT_CONNECT_TIMEOUT_SEC = 10;

    private static final long DEFAULT_IMAGE_INTERVAL = 60000L;
    private static final long CROSSFADE_DURATION = 2000L;

    // Power-on policy: try the PC Network Gallery for up to 5 seconds.
    // If it is not reachable, fall back once to the Internal Gallery.
    // After fallback, the server is not monitored in the background.
    private static final long STARTUP_NETWORK_WAIT_MS = 5000L;
    private static final int STARTUP_PROBE_TIMEOUT_MS = 800;

    // Image duration is session-only. It always resets to 1 minute
    // whenever the app is restarted.
    private long imageInterval = DEFAULT_IMAGE_INTERVAL;

    private static final int MODE_LOCAL = 0;
    private static final int MODE_NETWORK = 1;
    private static final int MODE_ART = 2;

    private String currentArtFileName = null;

    private final List<File> artFiles = new ArrayList<File>();
    private int artIndex = -1;

    private static final long RIGHT_CLICK_DEBOUNCE_MS = 400L;

    // ------------------------------------------------------------
    // Network configuration
    // ------------------------------------------------------------

    private String networkHost =
            DEFAULT_NETWORK_HOST;

    private int networkPort =
            DEFAULT_NETWORK_PORT;

    private int connectTimeoutSec =
            DEFAULT_CONNECT_TIMEOUT_SEC;

    private int maxMediaFiles = 100;
    private long minFreeMb = 200;
    private String trustedServer =
            "EO1M-8F29C74A";

    private volatile boolean networkSyncStarted = false;

    // ------------------------------------------------------------
    // Views
    // ------------------------------------------------------------

    private ImageView imageView;
    private ImageView imageViewNext;
    private VideoView videoView;
    private WebView webView;
    private ProgressBar progressBar;
    private TextView clockView;
    private TextView syncStatusView;

    // ------------------------------------------------------------
    // Media
    // ------------------------------------------------------------

    private final List<File> mediaFiles =
            new ArrayList<File>();

    private int mediaIndex = -1;

    private final Handler handler =
            new Handler();

    private final Runnable nextImageRunnable =
            new Runnable() {
                @Override
                public void run() {

                    writeLog(
                            "TIMER showNextMedia()"
                    );

                    showNextMedia();
                }
            };

    // ------------------------------------------------------------
    // Network Gallery
    // ------------------------------------------------------------

    private final Handler networkHandler =
            new Handler();

    private boolean networkPageLoaded = false;

    private boolean networkErrorDialogVisible =
            false;

    private final Runnable networkTimeoutRunnable =
            new Runnable() {

                @Override
                public void run() {

                    if (currentMode != MODE_NETWORK) {
                        return;
                    }

                    if (!networkPageLoaded) {

                        writeLog(
                                "Network Gallery timeout"
                        );

                        webView.stopLoading();

                        showNetworkErrorDialog();
                    }
                }
            };

    // ------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------

    private boolean clockVisible = false;

    private final Handler clockHandler =
            new Handler();

    private final Runnable clockRunnable =
            new Runnable() {

                @Override
                public void run() {

                    if (!clockVisible) {
                        return;
                    }

                    SimpleDateFormat sdf =
                            new SimpleDateFormat(
                                    "HH:mm",
                                    Locale.getDefault()
                            );

                    clockView.setText(
                            sdf.format(new Date())
                    );

                    long now =
                            System.currentTimeMillis();

                    long delay =
                            60000L -
                                    (now % 60000L) +
                                    100L;

                    clockHandler.postDelayed(
                            this,
                            delay
                    );
                }
            };

    // ------------------------------------------------------------
    // State
    // ------------------------------------------------------------

    /*
     * Every fresh app start begins in Local Gallery.
     * Network Gallery mode is session-only.
     */
    private int currentMode = MODE_LOCAL;

    private boolean firstImageActive = true;

    private boolean hasCurrentImage = false;

    private long lastRightClickTime = 0L;

    private AlertDialog controlDialog;

    // ------------------------------------------------------------
    // Activity lifecycle
    // ------------------------------------------------------------

    @Override
    protected void onCreate(
            Bundle savedInstanceState) {

        super.onCreate(savedInstanceState);

        setContentView(
                R.layout.activity_main
        );

        imageView =
                (ImageView)
                        findViewById(
                                R.id.imageView
                        );

        imageViewNext =
                (ImageView)
                        findViewById(
                                R.id.imageViewNext
                        );

        videoView =
                (VideoView)
                        findViewById(
                                R.id.videoView
                        );

        webView =
                (WebView)
                        findViewById(
                                R.id.webView
                        );

        progressBar =
                (ProgressBar)
                        findViewById(
                                R.id.progressBar
                        );

        clockView =
                (TextView)
                        findViewById(
                                R.id.clockView
                        );

        syncStatusView =
                (TextView)
                        findViewById(
                                R.id.syncStatusView
                        );

        startNewLog();

        writeLog("onCreate");

        loadConfig();

        setupWebView();
        setupVideoView();

        /*
         * Power-on default is Network Gallery.  We first probe the PC server
         * for a short, bounded period.  If it is unavailable, fall back once
         * to Internal Gallery and do not keep polling in the background.
         */
        currentMode = MODE_NETWORK;

        /*
         * Clock always starts ON.
         */
        clockVisible = true;

        clockView.setVisibility(
                View.VISIBLE
        );

        clockView.bringToFront();

        clockHandler.post(
                clockRunnable
        );

        startPowerOnGallery();
    }

    @Override
    protected void onResume() {

        super.onResume();

        writeLog("onResume");

        if ((currentMode == MODE_LOCAL || currentMode == MODE_ART) &&
                videoView.getVisibility() ==
                        View.VISIBLE &&
                !videoView.isPlaying()) {

            try {
                videoView.start();
            } catch (Exception ignored) {
            }
        }
    }

    @Override
    protected void onPause() {

        super.onPause();

        writeLog("onPause");

        handler.removeCallbacks(
                nextImageRunnable
        );

        if (videoView != null &&
                videoView.isPlaying()) {

            videoView.pause();
        }
    }

    @Override
    protected void onDestroy() {

        writeLog("onDestroy");

        handler.removeCallbacks(
                nextImageRunnable
        );

        networkHandler.removeCallbacks(
                networkTimeoutRunnable
        );

        clockHandler.removeCallbacks(
                clockRunnable
        );

        if (videoView != null) {

            videoView.stopPlayback();
        }

        if (webView != null) {

            webView.stopLoading();
        }

        if (controlDialog != null) {

            controlDialog.dismiss();

            controlDialog = null;
        }

        super.onDestroy();
    }

    // ------------------------------------------------------------
    // Configuration
    // ------------------------------------------------------------

    private void loadConfig() {

        File configFile =
                new File(CONFIG_FILE);

        /*
         * First run:
         * create .config with safe defaults.
         */
        if (!configFile.exists()) {

            writeLog(
                    "Config not found; " +
                            "creating defaults"
            );

            saveConfig();

            return;
        }

        Properties props =
                new Properties();

        try {

            BufferedReader reader =
                    new BufferedReader(
                            new FileReader(
                                    configFile
                            )
                    );

            props.load(reader);

            reader.close();

            String host =
                    props.getProperty(
                            "NETWORK_HOST"
                    );

            if (host != null &&
                    host.trim().length() > 0) {

                networkHost =
                        host.trim();
            }

            String port =
                    props.getProperty(
                            "NETWORK_PORT"
                    );

            if (port != null) {

                try {

                    int value =
                            Integer.parseInt(
                                    port.trim()
                            );

                    if (value >= 1 &&
                            value <= 65535) {

                        networkPort = value;
                    }

                } catch (Exception ignored) {
                }
            }

            String timeout =
                    props.getProperty(
                            "CONNECT_TIMEOUT_SEC"
                    );

            if (timeout != null) {

                try {

                    int value =
                            Integer.parseInt(
                                    timeout.trim()
                            );

                    if (value >= 1) {

                        connectTimeoutSec =
                                value;
                    }

                } catch (Exception ignored) {
                }
            }

            String maxFiles = props.getProperty("MAX_MEDIA_FILES");
            if (maxFiles != null) {
                try {
                    int value = Integer.parseInt(maxFiles.trim());
                    if (value >= 1) maxMediaFiles = value;
                } catch (Exception ignored) {
                }
            }

            String minFree = props.getProperty("MIN_FREE_MB");
            if (minFree != null) {
                try {
                    long value = Long.parseLong(minFree.trim());
                    if (value >= 0) minFreeMb = value;
                } catch (Exception ignored) {
                }
            }

            String trusted = props.getProperty("TRUSTED_SERVER");
            if (trusted != null && trusted.trim().length() > 0) {
                trustedServer = trusted.trim();
            }

            writeLog(
                    "Config loaded: " +
                            networkHost +
                            ":" +
                            networkPort +
                            " timeout=" +
                            connectTimeoutSec +
                            " max=" + maxMediaFiles +
                            " minFreeMB=" + minFreeMb +
                            " trusted=" + trustedServer
            );

        } catch (Exception e) {

            writeLog(
                    "Config read error: " +
                            e.getMessage()
            );
        }
    }

    private void saveConfig() {

        File configFile =
                new File(CONFIG_FILE);

        File parent =
                configFile.getParentFile();

        if (parent != null &&
                !parent.exists()) {

            parent.mkdirs();
        }

        /*
         * Preserve values that will be used
         * by the Safe Sync implementation.
         */
        String maxMediaFilesValue = String.valueOf(maxMediaFiles);
        String minFreeMbValue = String.valueOf(minFreeMb);
        String trustedServerValue = trustedServer;

        if (configFile.exists()) {

            Properties oldProps =
                    new Properties();

            try {

                BufferedReader reader =
                        new BufferedReader(
                                new FileReader(
                                        configFile
                                )
                        );

                oldProps.load(reader);

                reader.close();

                maxMediaFilesValue =
                        oldProps.getProperty(
                                "MAX_MEDIA_FILES",
                                maxMediaFilesValue
                        );

                minFreeMbValue =
                        oldProps.getProperty(
                                "MIN_FREE_MB",
                                minFreeMbValue
                        );

                trustedServerValue =
                        oldProps.getProperty(
                                "TRUSTED_SERVER",
                                trustedServerValue
                        );

            } catch (Exception ignored) {
            }
        }

        try {

            FileWriter writer =
                    new FileWriter(
                            configFile,
                            false
                    );

            writer.write(
                    "# EO1-Museum v0.4 configuration\n"
            );

            writer.write(
                    "NETWORK_HOST=" +
                            networkHost +
                            "\n"
            );

            writer.write(
                    "NETWORK_PORT=" +
                            networkPort +
                            "\n"
            );

            writer.write(
                    "CONNECT_TIMEOUT_SEC=" +
                            connectTimeoutSec +
                            "\n"
            );

            writer.write(
                    "MAX_MEDIA_FILES=" +
                            maxMediaFilesValue +
                            "\n"
            );

            writer.write(
                    "MIN_FREE_MB=" +
                            minFreeMbValue +
                            "\n"
            );

            writer.write(
                    "TRUSTED_SERVER=" +
                            trustedServerValue +
                            "\n"
            );

            writer.close();

            writeLog("Config saved");

        } catch (Exception e) {

            writeLog(
                    "Config write error: " +
                            e.getMessage()
            );
        }
    }

    private String getNetworkGalleryUrl() {

        return "http://" +
                networkHost +
                ":" +
                networkPort +
                "/";
    }

    // ------------------------------------------------------------
    // Power-on Network-first startup
    // ------------------------------------------------------------

    private void startPowerOnGallery() {

        writeLog("Power-on: probing Network Gallery for up to 5 seconds");

        // Keep a clean black screen while Wi-Fi/server availability is tested.
        imageView.setVisibility(View.GONE);
        imageViewNext.setVisibility(View.GONE);
        videoView.setVisibility(View.GONE);
        webView.setVisibility(View.GONE);
        showProgress();
        showSyncMessage("Connecting to PC Gallery...", 0L);

        new Thread(new Runnable() {
            @Override
            public void run() {

                final long deadline = SystemClock.elapsedRealtime()
                        + STARTUP_NETWORK_WAIT_MS;
                boolean reachable = false;

                while (SystemClock.elapsedRealtime() < deadline) {
                    if (isNetworkGalleryReachable()) {
                        reachable = true;
                        break;
                    }

                    try {
                        Thread.sleep(250L);
                    } catch (InterruptedException ignored) {
                        break;
                    }
                }

                final boolean serverAvailable = reachable;

                runOnUiThread(new Runnable() {
                    @Override
                    public void run() {

                        if (serverAvailable) {
                            writeLog("Power-on: Network Gallery available");
                            showSyncMessage("PC Gallery connected", 1200L);
                            showNetworkMode();
                        } else {
                            writeLog("Power-on: Network Gallery unavailable; fallback to Internal Gallery");
                            hideProgress();
                            showSyncMessage(
                                    "PC Gallery unavailable - switching to Internal Gallery...",
                                    1400L);

                            handler.postDelayed(new Runnable() {
                                @Override
                                public void run() {
                                    showLocalMode();
                                }
                            }, 1400L);
                        }
                    }
                });
            }
        }, "EO1-StartupProbe").start();
    }

    private boolean isNetworkGalleryReachable() {

        HttpURLConnection connection = null;

        try {
            connection = (HttpURLConnection)
                    new URL(getNetworkGalleryUrl()).openConnection();
            connection.setConnectTimeout(STARTUP_PROBE_TIMEOUT_MS);
            connection.setReadTimeout(STARTUP_PROBE_TIMEOUT_MS);
            connection.setUseCaches(false);
            connection.setInstanceFollowRedirects(true);
            connection.setRequestMethod("GET");
            connection.connect();

            int code = connection.getResponseCode();
            return code >= 200 && code < 400;

        } catch (Exception e) {
            return false;

        } finally {
            if (connection != null) connection.disconnect();
        }
    }

    // ------------------------------------------------------------
    // WebView / Network Gallery
    // ------------------------------------------------------------

    private void setupWebView() {

        webView.setBackgroundColor(
                Color.BLACK
        );

        webView.getSettings()
                .setJavaScriptEnabled(true);

        /*
         * Android 4.4 / API 19 compatible
         * WebViewClient.
         */
        webView.setWebViewClient(
                new WebViewClient() {

                    @Override
                    public void onPageFinished(
                            WebView view,
                            String url) {

                        super.onPageFinished(
                                view,
                                url
                        );

                        if (currentMode !=
                                MODE_NETWORK) {

                            return;
                        }

                        networkPageLoaded = true;

                        networkHandler
                                .removeCallbacks(
                                        networkTimeoutRunnable
                                );

                        hideProgress();

                        writeLog(
                                "Network Gallery loaded: " +
                                        url
                        );

                        startNetworkSync();
                    }

                    @Override
                    public void onReceivedError(
                            WebView view,
                            int errorCode,
                            String description,
                            String failingUrl) {

                        super.onReceivedError(
                                view,
                                errorCode,
                                description,
                                failingUrl
                        );

                        /*
                         * On Android 4.4 this callback may
                         * also be caused by a subresource.
                         *
                         * Therefore the timeout, rather
                         * than this callback alone, decides
                         * whether the Network Gallery has
                         * failed.
                         */
                        writeLog(
                                "WebView error=" +
                                        errorCode +
                                        " " +
                                        description +
                                        " url=" +
                                        failingUrl
                        );
                    }
                }
        );
    }

    // ------------------------------------------------------------
    // Safe Sync: PC Network Gallery -> EO1 Local Gallery
    // ------------------------------------------------------------

    private void startNetworkSync() {

        if (networkSyncStarted) return;
        networkSyncStarted = true;

        new Thread(new Runnable() {
            @Override
            public void run() {
                syncNetworkGallery();
            }
        }, "EO1-SafeSync").start();
    }

    private void syncNetworkGallery() {

        final String baseUrl = getNetworkGalleryUrl();
        writeLog("Safe Sync control check: " + baseUrl + "eo1-status");

        try {
            String status = downloadText(baseUrl + "eo1-status");
            String[] lines = status.split("\\r?\\n");
            String serverId = lines.length > 0 ? lines[0].trim() : "";
            boolean syncRequested = false;

            for (String line : lines) {
                if ("SYNC=1".equalsIgnoreCase(line.trim())) {
                    syncRequested = true;
                }
            }

            if (trustedServer != null && trustedServer.length() > 0 &&
                    !trustedServer.equals(serverId)) {
                writeLog("Safe Sync refused: TRUSTED_SERVER mismatch: " + serverId);
                showSyncMessage("Sync refused: untrusted server", 4000L);
                return;
            }

            if (!syncRequested) {
                writeLog("Safe Sync not requested by server");
                return;
            }

            writeLog("Safe Sync start: " + baseUrl +
                    " trusted=" + trustedServer);
            showSyncMessage("Syncing...", 0L);

            String js = downloadText(baseUrl + "images.js");
            List<String> paths = parseImagePaths(js);

            if (paths.isEmpty()) {
                writeLog("Safe Sync: images.js contains no display images");
                showSyncMessage("Sync stopped: no images", 4000L);
                return;
            }

            int limit = Math.min(paths.size(), maxMediaFiles);
            File mediaDir = new File(MEDIA_DIR);
            if (!mediaDir.exists() && !mediaDir.mkdirs()) {
                writeLog("Safe Sync: cannot create " + MEDIA_DIR);
                showSyncMessage("Sync failed: storage unavailable", 5000L);
                return;
            }

            int completed = 0;
            boolean stoppedForSpace = false;
            for (int i = 0; i < limit; i++) {
                String relativePath = paths.get(i);
                String fileName = new File(relativePath).getName();

                if (fileName.length() == 0) continue;

                if (!hasReserveSpace(mediaDir, 0)) {
                    writeLog("Safe Sync stopped: MIN_FREE_MB=" + minFreeMb);
                    stoppedForSpace = true;
                    break;
                }

                showSyncMessage("Syncing... " + (i + 1) + " / " + limit, 0L);

                File target = new File(mediaDir, fileName);
                File temp = new File(mediaDir, fileName + ".tmp");

                if (downloadFileSafely(
                        baseUrl + relativePath,
                        temp,
                        target,
                        mediaDir)) {
                    completed++;
                    writeLog("Safe Sync: " + fileName +
                            " (" + completed + "/" + limit + ")");
                } else {
                    writeLog("Safe Sync failed: " + relativePath);
                }
            }

            writeLog("Safe Sync complete: " + completed +
                    "/" + limit + " files");

            if (stoppedForSpace) {
                showSyncMessage("Sync stopped: free space limit (" +
                        completed + " / " + limit + ")", 6000L);
            } else if (completed == limit) {
                showSyncMessage("Sync complete: " + completed + " images", 4000L);
            } else {
                showSyncMessage("Sync finished: " + completed +
                        " / " + limit, 5000L);
            }

        } catch (Exception e) {
            writeLog("Safe Sync error: " + e.getMessage());
            showSyncMessage("Sync error: " + e.getMessage(), 5000L);
        }
    }

    private void showSyncMessage(final String message, final long hideAfterMs) {
        runOnUiThread(new Runnable() {
            @Override
            public void run() {
                if (syncStatusView == null) return;
                syncStatusView.setText(message);
                syncStatusView.setVisibility(View.VISIBLE);
                syncStatusView.bringToFront();

                if (clockVisible && clockView != null) {
                    clockView.bringToFront();
                }

                syncStatusView.removeCallbacks(hideSyncStatusRunnable);
                if (hideAfterMs > 0) {
                    syncStatusView.postDelayed(hideSyncStatusRunnable, hideAfterMs);
                }
            }
        });
    }

    private final Runnable hideSyncStatusRunnable = new Runnable() {
        @Override
        public void run() {
            if (syncStatusView != null) {
                syncStatusView.setVisibility(View.GONE);
            }
        }
    };

    private String downloadText(String urlString) throws IOException {
        HttpURLConnection connection = null;
        BufferedReader reader = null;
        try {
            connection = (HttpURLConnection) new URL(urlString).openConnection();
            connection.setConnectTimeout(connectTimeoutSec * 1000);
            connection.setReadTimeout(connectTimeoutSec * 1000);
            connection.setUseCaches(false);
            connection.connect();

            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
                throw new IOException("HTTP " + connection.getResponseCode());
            }

            reader = new BufferedReader(
                    new java.io.InputStreamReader(connection.getInputStream(), "UTF-8"));
            StringBuilder result = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                result.append(line).append('\n');
            }
            return result.toString();
        } finally {
            if (reader != null) try { reader.close(); } catch (Exception ignored) {}
            if (connection != null) connection.disconnect();
        }
    }

    private List<String> parseImagePaths(String js) {
        List<String> result = new ArrayList<String>();
        Pattern pattern = Pattern.compile("[\\\"'](display/[^\\\"']+)[\\\"']");
        Matcher matcher = pattern.matcher(js);
        while (matcher.find() && result.size() < maxMediaFiles) {
            String path = matcher.group(1).replace("\\\\", "/");
            if (!path.contains("..")) result.add(path);
        }
        return result;
    }

    private boolean downloadFileSafely(
            String urlString,
            File temp,
            File target,
            File mediaDir) {

        HttpURLConnection connection = null;
        InputStream in = null;
        BufferedOutputStream out = null;

        try {
            connection = (HttpURLConnection) new URL(urlString).openConnection();
            connection.setConnectTimeout(connectTimeoutSec * 1000);
            connection.setReadTimeout(connectTimeoutSec * 1000);
            connection.setUseCaches(false);
            connection.connect();

            if (connection.getResponseCode() != HttpURLConnection.HTTP_OK) {
                return false;
            }

            long contentLength = connection.getContentLength();
            if (contentLength > 0 && !hasReserveSpace(mediaDir, contentLength)) {
                writeLog("Safe Sync skipped for free-space reserve: " + target.getName());
                return false;
            }

            if (temp.exists()) temp.delete();

            in = new BufferedInputStream(connection.getInputStream());
            out = new BufferedOutputStream(new FileOutputStream(temp, false));

            byte[] buffer = new byte[32768];
            int count;
            while ((count = in.read(buffer)) != -1) {
                out.write(buffer, 0, count);
            }
            out.flush();
            out.close();
            out = null;
            in.close();
            in = null;

            if (contentLength > 0 && temp.length() != contentLength) {
                temp.delete();
                return false;
            }

            // Same filename always means replace.  The old file is kept
            // until the new download has completed successfully.
            if (target.exists() && !target.delete()) {
                temp.delete();
                return false;
            }

            if (!temp.renameTo(target)) {
                temp.delete();
                return false;
            }

            return true;

        } catch (Exception e) {
            writeLog("Safe Sync download error: " + e.getMessage());
            if (temp.exists()) temp.delete();
            return false;
        } finally {
            if (out != null) try { out.close(); } catch (Exception ignored) {}
            if (in != null) try { in.close(); } catch (Exception ignored) {}
            if (connection != null) connection.disconnect();
        }
    }

    private boolean hasReserveSpace(File dir, long incomingBytes) {
        try {
            StatFs stat = new StatFs(dir.getAbsolutePath());
            long available = (long) stat.getAvailableBlocks() *
                    (long) stat.getBlockSize();
            long reserve = minFreeMb * 1024L * 1024L;
            return available - incomingBytes >= reserve;
        } catch (Exception e) {
            writeLog("Safe Sync free-space check error: " + e.getMessage());
            return false;
        }
    }

    // ------------------------------------------------------------
    // VideoView
    // ------------------------------------------------------------

    private void setupVideoView() {

        videoView.setOnPreparedListener(
                mp -> {

                    writeLog(
                            "Video prepared"
                    );

                    hideProgress();

                    try {

                        videoView.start();

                        writeLog(
                                "Video started"
                        );

                    } catch (Exception e) {

                        writeLog(
                                "Video start error: " +
                                        e.getMessage()
                        );

                        hideProgress();

                        if (currentMode == MODE_ART) {
                            showNextArt();
                        } else {
                            showNextMedia();
                        }
                    }
                }
        );

        videoView.setOnCompletionListener(
                mp -> {

                    writeLog(
                            "Video completed"
                    );

                    hideProgress();

                    if (currentMode == MODE_ART) {
                        showNextArt();
                    } else {
                        showNextMedia();
                    }
                }
        );

        videoView.setOnErrorListener(
                (mp, what, extra) -> {

                    writeLog(
                            "Video error what=" +
                                    what +
                                    " extra=" +
                                    extra
                    );

                    hideProgress();

                    Toast.makeText(
                            MainActivity.this,
                            "Video playback error",
                            Toast.LENGTH_SHORT
                    ).show();

                    handler.postDelayed(
                            new Runnable() {

                                @Override
                                public void run() {

                                    if (currentMode == MODE_ART) {
                                        showNextArt();
                                    } else {
                                        showNextMedia();
                                    }
                                }
                            },
                            500
                    );

                    return true;
                }
        );
    }

    // ------------------------------------------------------------
    // Local Gallery mode
    // ------------------------------------------------------------

    private void showLocalMode() {

        writeLog(
                "showLocalMode"
        );

        currentMode = MODE_LOCAL;

        networkHandler.removeCallbacks(
                networkTimeoutRunnable
        );

        networkPageLoaded = false;

        handler.removeCallbacks(
                nextImageRunnable
        );

        hideProgress();

        webView.stopLoading();

        webView.setVisibility(
                View.GONE
        );

        try {

            videoView.stopPlayback();

        } catch (Exception ignored) {
        }

        videoView.setVisibility(
                View.GONE
        );

        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setAlpha(1f);
        imageViewNext.setAlpha(0f);

        imageView.setVisibility(
                View.INVISIBLE
        );

        imageViewNext.setVisibility(
                View.INVISIBLE
        );

        firstImageActive = true;
        hasCurrentImage = false;

        loadMediaList();

        if (mediaFiles.isEmpty()) {

            imageView.setVisibility(
                    View.GONE
            );

            imageViewNext.setVisibility(
                    View.GONE
            );

            Toast.makeText(
                    this,
                    "No media files found",
                    Toast.LENGTH_LONG
            ).show();

            return;
        }

        mediaIndex = -1;

        showNextMedia();
    }

    private void loadMediaList() {

        mediaFiles.clear();

        File dir =
                new File(MEDIA_DIR);

        if (!dir.exists() ||
                !dir.isDirectory()) {

            writeLog(
                    "Media directory not found: " +
                            MEDIA_DIR
            );

            return;
        }

        File[] files =
                dir.listFiles();

        if (files == null) {

            writeLog(
                    "Media directory listFiles() " +
                            "returned null"
            );

            return;
        }

        for (File file : files) {

            if (!file.isFile()) {
                continue;
            }

            String name =
                    file.getName()
                            .toLowerCase(
                                    Locale.US
                            );

            if (name.endsWith(".jpg") ||
                    name.endsWith(".jpeg") ||
                    name.endsWith(".png") ||
                    name.endsWith(".mp4")) {

                mediaFiles.add(file);
            }
        }

        Collections.shuffle(
                mediaFiles
        );

        writeLog(
                "Media files found=" +
                        mediaFiles.size()
        );
    }

    private void showNextMedia() {

        if (currentMode != MODE_LOCAL) {
            return;
        }

        handler.removeCallbacks(
                nextImageRunnable
        );

        hideProgress();

        if (mediaFiles.isEmpty()) {

            writeLog(
                    "showNextMedia: " +
                            "media list empty"
            );

            loadMediaList();

            if (mediaFiles.isEmpty()) {
                return;
            }
        }

        mediaIndex++;

        if (mediaIndex >=
                mediaFiles.size()) {

            Collections.shuffle(
                    mediaFiles
            );

            mediaIndex = 0;

            writeLog(
                    "Media list reshuffled"
            );
        }

        File file =
                mediaFiles.get(
                        mediaIndex
                );

        writeLog(
                "Showing media: " +
                        file.getName()
        );

        String name =
                file.getName()
                        .toLowerCase(
                                Locale.US
                        );

        if (name.endsWith(".mp4")) {

            showVideo(file);

        } else {

            showImage(file);
        }
    }

    private void showImage(
            File file) {

        hideProgress();

        try {

            videoView.stopPlayback();

        } catch (Exception ignored) {
        }

        videoView.setVisibility(
                View.GONE
        );

        webView.setVisibility(
                View.GONE
        );

        handler.removeCallbacks(
                nextImageRunnable
        );

        /*
         * First image after entering
         * Local Gallery:
         * display immediately.
         */
        if (!hasCurrentImage) {

            imageView.animate().cancel();

            imageViewNext.animate()
                    .cancel();

            imageView.setImageURI(null);

            imageView.setImageURI(
                    Uri.fromFile(file)
            );

            imageView.setAlpha(1f);

            imageView.setVisibility(
                    View.VISIBLE
            );

            imageViewNext.setAlpha(0f);

            imageViewNext.setVisibility(
                    View.INVISIBLE
            );

            firstImageActive = true;
            hasCurrentImage = true;

        } else {

            final ImageView oldView =
                    firstImageActive
                            ? imageView
                            : imageViewNext;

            final ImageView newView =
                    firstImageActive
                            ? imageViewNext
                            : imageView;

            oldView.animate().cancel();

            newView.animate().cancel();

            newView.setImageURI(null);

            newView.setImageURI(
                    Uri.fromFile(file)
            );

            newView.setAlpha(0f);

            newView.setVisibility(
                    View.VISIBLE
            );

            oldView.setVisibility(
                    View.VISIBLE
            );

            oldView.setAlpha(1f);

            newView.animate()
                    .alpha(1f)
                    .setDuration(
                            CROSSFADE_DURATION
                    )
                    .start();

            oldView.animate()
                    .alpha(0f)
                    .setDuration(
                            CROSSFADE_DURATION
                    )
                    .withEndAction(
                            new Runnable() {

                                @Override
                                public void run() {

                                    oldView.setVisibility(
                                            View.INVISIBLE
                                    );
                                }
                            }
                    )
                    .start();

            firstImageActive =
                    !firstImageActive;
        }

        handler.postDelayed(
                nextImageRunnable,
                imageInterval
        );

        writeLog(
                "Image timer scheduled: " +
                        imageInterval +
                        " ms"
        );
    }

    private void showVideo(
            File file) {

        handler.removeCallbacks(
                nextImageRunnable
        );

        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setVisibility(
                View.GONE
        );

        imageViewNext.setVisibility(
                View.GONE
        );

        hasCurrentImage = false;
        firstImageActive = true;

        videoView.setVisibility(
                View.VISIBLE
        );

        showProgress();

        try {

            videoView.stopPlayback();

            videoView.setVideoURI(
                    Uri.fromFile(file)
            );

            videoView.requestFocus();

        } catch (Exception e) {

            writeLog(
                    "showVideo exception: " +
                            e.getMessage()
            );

            hideProgress();

            showNextMedia();
        }
    }

    // ------------------------------------------------------------
    // Art mode: shuffled local MP4 playback
    // ------------------------------------------------------------

    private void showArtMode() {

        writeLog("showArtMode");

        currentMode = MODE_ART;
        currentArtFileName = null;

        handler.removeCallbacks(nextImageRunnable);
        networkHandler.removeCallbacks(networkTimeoutRunnable);
        networkPageLoaded = false;

        hideProgress();

        webView.stopLoading();
        webView.setVisibility(View.GONE);

        imageView.animate().cancel();
        imageViewNext.animate().cancel();
        imageView.setVisibility(View.GONE);
        imageViewNext.setVisibility(View.GONE);

        hasCurrentImage = false;
        firstImageActive = true;

        loadArtList();

        if (artFiles.isEmpty()) {
            try { videoView.stopPlayback(); } catch (Exception ignored) {}
            videoView.setVisibility(View.GONE);

            Toast.makeText(this,
                    "No MP4 art found in:\n" + ART_DIR,
                    Toast.LENGTH_LONG).show();
            writeLog("No MP4 art found in: " + ART_DIR);
            return;
        }

        artIndex = -1;
        showNextArt();
    }

    private void loadArtList() {

        artFiles.clear();

        File artDir = new File(ART_DIR);
        if (!artDir.exists() || !artDir.isDirectory()) {
            writeLog("Art directory not found: " + ART_DIR);
            return;
        }

        File[] files = artDir.listFiles();
        if (files == null) {
            writeLog("Art directory listFiles() returned null");
            return;
        }

        for (File file : files) {
            if (!file.isFile()) continue;

            String name = file.getName().toLowerCase(Locale.US);
            if (name.endsWith(".mp4")) {
                artFiles.add(file);
            }
        }

        Collections.shuffle(artFiles);
        writeLog("Art MP4 files found=" + artFiles.size());
    }

    private void showNextArt() {

        if (currentMode != MODE_ART) return;

        hideProgress();

        if (artFiles.isEmpty()) {
            loadArtList();
            if (artFiles.isEmpty()) return;
        }

        artIndex++;
        if (artIndex >= artFiles.size()) {
            Collections.shuffle(artFiles);
            artIndex = 0;
            writeLog("Art list reshuffled");
        }

        File file = artFiles.get(artIndex);
        currentArtFileName = file.getName();
        writeLog("Playing Art MP4: " + file.getName());

        handler.removeCallbacks(nextImageRunnable);
        webView.stopLoading();
        webView.setVisibility(View.GONE);
        imageView.setVisibility(View.GONE);
        imageViewNext.setVisibility(View.GONE);

        videoView.setVisibility(View.VISIBLE);
        showProgress();

        try {
            videoView.stopPlayback();
            videoView.setVideoURI(Uri.fromFile(file));
            videoView.requestFocus();
        } catch (Exception e) {
            writeLog("Art video exception: " + e.getMessage());
            hideProgress();
            handler.postDelayed(new Runnable() {
                @Override
                public void run() {
                    showNextArt();
                }
            }, 500L);
        }

        if (clockVisible && clockView != null) {
            clockView.bringToFront();
        }
    }

    // ------------------------------------------------------------
    // Network Gallery mode
    // ------------------------------------------------------------

    private void showNetworkMode() {

        writeLog(
                "showNetworkMode"
        );

        currentMode = MODE_NETWORK;

        handler.removeCallbacks(
                nextImageRunnable
        );

        networkHandler.removeCallbacks(
                networkTimeoutRunnable
        );

        networkPageLoaded = false;
        networkSyncStarted = false;

        hideProgress();

        try {

            videoView.stopPlayback();

        } catch (Exception ignored) {
        }

        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setVisibility(
                View.GONE
        );

        imageViewNext.setVisibility(
                View.GONE
        );

        videoView.setVisibility(
                View.GONE
        );

        hasCurrentImage = false;
        firstImageActive = true;

        webView.setVisibility(
                View.VISIBLE
        );

        showProgress();

        String url =
                getNetworkGalleryUrl();

        writeLog(
                "Loading Network Gallery: " +
                        url
        );

        webView.stopLoading();

        /*
         * Avoid displaying a cached successful page
         * when the server is no longer reachable.
         */
        webView.clearCache(false);

        webView.loadUrl(url);

        networkHandler.postDelayed(
                networkTimeoutRunnable,
                connectTimeoutSec * 1000L
        );

        if (clockVisible &&
                clockView != null) {

            clockView.bringToFront();
        }
    }

    // ------------------------------------------------------------
    // Network address dialog
    // ------------------------------------------------------------

    private void showNetworkAddressDialog() {

        final EditText hostInput =
                new EditText(this);

        hostInput.setSingleLine(true);

        hostInput.setText(
                networkHost
        );

        hostInput.setHint(
                "192.168.1.103"
        );

        /*
         * Use normal text keyboard for host/IP.
         * Pure numeric keyboards on old Android
         * may make '.' inconvenient.
         */
        hostInput.setInputType(
                InputType.TYPE_CLASS_TEXT
        );

        final EditText portInput =
                new EditText(this);

        portInput.setSingleLine(true);

        portInput.setText(
                String.valueOf(
                        networkPort
                )
        );

        portInput.setHint(
                "8000"
        );

        portInput.setInputType(
                InputType.TYPE_CLASS_NUMBER
        );

        LinearLayout layout =
                new LinearLayout(this);

        layout.setOrientation(
                LinearLayout.VERTICAL
        );

        int padding =
                (int) (
                        24 *
                                getResources()
                                        .getDisplayMetrics()
                                        .density
                );

        layout.setPadding(
                padding,
                padding / 2,
                padding,
                0
        );

        TextView hostLabel =
                new TextView(this);

        hostLabel.setText(
                "Host / IP address"
        );

        layout.addView(
                hostLabel
        );

        layout.addView(
                hostInput
        );

        TextView portLabel =
                new TextView(this);

        portLabel.setText(
                "Port"
        );

        layout.addView(
                portLabel
        );

        layout.addView(
                portInput
        );

        final AlertDialog addressDialog =
                new AlertDialog.Builder(this)
                        .setTitle(
                                "Network Gallery Address"
                        )
                        .setView(layout)
                        .setNegativeButton(
                                "Cancel",
                                null
                        )
                        .setPositiveButton(
                                "Save",
                                null
                        )
                        .create();

        addressDialog.setOnShowListener(
                new DialogInterface
                        .OnShowListener() {

                    @Override
                    public void onShow(
                            DialogInterface d) {

                        addressDialog
                                .getButton(
                                        AlertDialog
                                                .BUTTON_POSITIVE
                                )
                                .setOnClickListener(
                                        new View
                                                .OnClickListener() {

                                            @Override
                                            public void onClick(
                                                    View v) {

                                                String newHost =
                                                        hostInput
                                                                .getText()
                                                                .toString()
                                                                .trim();

                                                String portText =
                                                        portInput
                                                                .getText()
                                                                .toString()
                                                                .trim();

                                                if (newHost.length()
                                                        == 0) {

                                                    Toast.makeText(
                                                            MainActivity.this,
                                                            "Enter a host or IP address",
                                                            Toast.LENGTH_SHORT
                                                    ).show();

                                                    return;
                                                }

                                                int newPort;

                                                try {

                                                    newPort =
                                                            Integer
                                                                    .parseInt(
                                                                            portText
                                                                    );

                                                } catch (
                                                        Exception e) {

                                                    Toast.makeText(
                                                            MainActivity.this,
                                                            "Invalid port",
                                                            Toast.LENGTH_SHORT
                                                    ).show();

                                                    return;
                                                }

                                                if (newPort < 1 ||
                                                        newPort >
                                                                65535) {

                                                    Toast.makeText(
                                                            MainActivity.this,
                                                            "Port must be 1-65535",
                                                            Toast.LENGTH_SHORT
                                                    ).show();

                                                    return;
                                                }

                                                networkHost =
                                                        newHost;

                                                networkPort =
                                                        newPort;

                                                saveConfig();

                                                writeLog(
                                                        "Network address changed: " +
                                                                getNetworkGalleryUrl()
                                                );

                                                Toast.makeText(
                                                        MainActivity.this,
                                                        "Network Gallery address saved",
                                                        Toast.LENGTH_SHORT
                                                ).show();

                                                addressDialog
                                                        .dismiss();

                                                if (currentMode ==
                                                        MODE_NETWORK) {

                                                    showNetworkMode();
                                                }
                                            }
                                        }
                                );
                    }
                }
        );

        addressDialog.show();

        hostInput.requestFocus();
    }

    // ------------------------------------------------------------
    // Network connection error dialog
    // ------------------------------------------------------------

    private void showNetworkErrorDialog() {

        if (currentMode != MODE_NETWORK) {
            return;
        }

        if (networkErrorDialogVisible) {
            return;
        }

        networkErrorDialogVisible = true;

        hideProgress();

        final String address =
                networkHost +
                        ":" +
                        networkPort;

        final AlertDialog dialog =
                new AlertDialog.Builder(this)
                        .setTitle(
                                "Cannot connect to Network Gallery"
                        )
                        .setMessage(
                                address +
                                        "\n\n" +
                                        "Check that the server is running " +
                                        "on the PC and that the Network " +
                                        "Gallery address is correct."
                        )
                        .setPositiveButton(
                                "Retry",
                                new DialogInterface
                                        .OnClickListener() {

                                    @Override
                                    public void onClick(
                                            DialogInterface dialog,
                                            int which) {

                                        networkErrorDialogVisible =
                                                false;

                                        showNetworkMode();
                                    }
                                }
                        )
                        .setNeutralButton(
                                "Address Settings",
                                new DialogInterface
                                        .OnClickListener() {

                                    @Override
                                    public void onClick(
                                            DialogInterface dialog,
                                            int which) {

                                        networkErrorDialogVisible =
                                                false;

                                        showNetworkAddressDialog();
                                    }
                                }
                        )
                        .setNegativeButton(
                                "Local Gallery",
                                new DialogInterface
                                        .OnClickListener() {

                                    @Override
                                    public void onClick(
                                            DialogInterface dialog,
                                            int which) {

                                        networkErrorDialogVisible =
                                                false;

                                        showLocalMode();
                                    }
                                }
                        )
                        .create();

        dialog.setOnDismissListener(
                new DialogInterface
                        .OnDismissListener() {

                    @Override
                    public void onDismiss(
                            DialogInterface dialog) {

                        networkErrorDialogVisible =
                                false;
                    }
                }
        );

        dialog.show();
    }

    // ------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------

    private void toggleClock() {

        clockVisible =
                !clockVisible;

        if (clockVisible) {

            clockView.setVisibility(
                    View.VISIBLE
            );

            clockView.bringToFront();

            clockHandler.removeCallbacks(
                    clockRunnable
            );

            clockHandler.post(
                    clockRunnable
            );

            writeLog(
                    "Clock ON"
            );

        } else {

            clockHandler.removeCallbacks(
                    clockRunnable
            );

            clockView.setVisibility(
                    View.GONE
            );

            writeLog(
                    "Clock OFF"
            );
        }
    }

    // ------------------------------------------------------------
    // Progress indicator
    // ------------------------------------------------------------

    private void showProgress() {

        if (progressBar != null) {

            progressBar.setVisibility(
                    View.VISIBLE
            );

            progressBar.bringToFront();

            if (clockVisible &&
                    clockView != null) {

                clockView.bringToFront();
            }
        }
    }

    private void hideProgress() {

        if (progressBar != null) {

            progressBar.setVisibility(
                    View.GONE
            );
        }
    }

    // ------------------------------------------------------------
    // Control menu
    // ------------------------------------------------------------

    private String getImageDurationLabel() {

        if (imageInterval == 15000L) return "15 sec";
        if (imageInterval == 30000L) return "30 sec";
        if (imageInterval == 120000L) return "2 min";
        return "1 min";
    }

    private void showImageDurationDialog() {

        final String[] labels = {
                "15 sec",
                "30 sec",
                "1 min",
                "2 min"
        };

        final long[] values = {
                15000L,
                30000L,
                60000L,
                120000L
        };

        int checked = 2;
        for (int i = 0; i < values.length; i++) {
            if (values[i] == imageInterval) {
                checked = i;
                break;
            }
        }

        new AlertDialog.Builder(this)
                .setTitle("Image duration")
                .setSingleChoiceItems(
                        labels,
                        checked,
                        new DialogInterface.OnClickListener() {
                            @Override
                            public void onClick(
                                    DialogInterface dialog,
                                    int which) {

                                imageInterval = values[which];

                                // Apply the new duration immediately to the
                                // currently displayed still image. Videos are
                                // unaffected and continue until completion.
                                if (currentMode == MODE_LOCAL &&
                                        videoView.getVisibility() != View.VISIBLE) {
                                    handler.removeCallbacks(nextImageRunnable);
                                    handler.postDelayed(
                                            nextImageRunnable,
                                            imageInterval
                                    );
                                }

                                writeLog(
                                        "Image duration changed: " +
                                                imageInterval +
                                                " ms"
                                );

                                Toast.makeText(
                                        MainActivity.this,
                                        "Image duration: " + labels[which],
                                        Toast.LENGTH_SHORT
                                ).show();

                                dialog.dismiss();
                            }
                        }
                )
                .setNegativeButton("Cancel", null)
                .show();
    }

    private void showControlMenu() {

        writeLog(
                "showControlMenu entered"
        );

        if (controlDialog != null &&
                controlDialog.isShowing()) {

            writeLog(
                    "Control dialog already visible"
            );

            return;
        }

        final String[] items = {

                currentMode == MODE_LOCAL
                        ? "✓ Local Gallery"
                        : "Local Gallery",

                currentMode == MODE_NETWORK
                        ? "✓ Network Gallery"
                        : "Network Gallery",

                currentMode == MODE_ART
                        ? "✓ Art"
                        : "Art",

                "Network Gallery Address",

                "Image duration: " + getImageDurationLabel(),

                "Next",

                "Rescan Media",

                clockVisible
                        ? "Clock: Off"
                        : "Clock: On"
        };

        /*
         * Next is available in Local Gallery and Art mode.
         * Rescan Media is available only in Local Gallery.
         */
        final ArrayAdapter<String> adapter =
                new ArrayAdapter<String>(
                        this,
                        android.R.layout
                                .simple_list_item_1,
                        items
                ) {

                    @Override
                    public boolean isEnabled(
                            int position) {

                        if (position == 5) {
                            return currentMode == MODE_LOCAL ||
                                    currentMode == MODE_ART;
                        }

                        if (position == 6) {
                            return currentMode == MODE_LOCAL;
                        }

                        return true;
                    }

                    @Override
                    public View getView(
                            int position,
                            View convertView,
                            ViewGroup parent) {

                        View view =
                                super.getView(
                                        position,
                                        convertView,
                                        parent
                                );

                        TextView textView =
                                (TextView)
                                        view.findViewById(
                                                android.R.id.text1
                                        );

                        if (isEnabled(position)) {

                            textView.setAlpha(
                                    1.0f
                            );

                        } else {

                            textView.setAlpha(
                                    0.45f
                            );
                        }

                        return view;
                    }
                };

        AlertDialog.Builder builder =
                new AlertDialog.Builder(this);

        builder.setTitle(
                "EO1 Museum"
        );

        builder.setAdapter(
                adapter,
                new DialogInterface
                        .OnClickListener() {

                    @Override
                    public void onClick(
                            DialogInterface dialog,
                            int which) {

                        writeLog(
                                "Menu selected=" +
                                        items[which]
                        );

                        switch (which) {

                            case 0:

                                showLocalMode();

                                break;

                            case 1:

                                showNetworkMode();

                                break;

                            case 2:

                                showArtMode();

                                break;

                            case 3:

                                showNetworkAddressDialog();

                                break;

                            case 4:

                                showImageDurationDialog();

                                break;

                            case 5:

                                if (currentMode == MODE_LOCAL) {
                                    showNextMedia();
                                } else if (currentMode == MODE_ART) {
                                    showNextArt();
                                }

                                break;

                            case 6:

                                if (currentMode ==
                                        MODE_LOCAL) {

                                    loadMediaList();

                                    mediaIndex = -1;

                                    showNextMedia();

                                    Toast.makeText(
                                            MainActivity.this,
                                            "Media rescanned",
                                            Toast.LENGTH_SHORT
                                    ).show();
                                }

                                break;

                            case 7:

                                toggleClock();

                                break;
                        }
                    }
                }
        );

        builder.setOnDismissListener(
                new DialogInterface
                        .OnDismissListener() {

                    @Override
                    public void onDismiss(
                            DialogInterface dialog) {

                        writeLog(
                                "Control dialog dismissed"
                        );

                        controlDialog = null;
                    }
                }
        );

        controlDialog =
                builder.create();

        controlDialog.show();

        writeLog(
                "Control dialog shown"
        );
    }

    // ------------------------------------------------------------
    // Mouse
    // ------------------------------------------------------------

    private boolean isMouseEvent(
            MotionEvent event) {

        return (event.getSource() &
                android.view.InputDevice
                        .SOURCE_MOUSE)
                ==
                android.view.InputDevice
                        .SOURCE_MOUSE;
    }

    private boolean isRightButton(
            MotionEvent event) {

        return (event.getButtonState() &
                MotionEvent.BUTTON_SECONDARY)
                != 0;
    }

    private boolean handleRightClick(
            MotionEvent event,
            String origin) {

        if (!isMouseEvent(event)) {
            return false;
        }

        if (!isRightButton(event)) {
            return false;
        }

        long now =
                SystemClock
                        .elapsedRealtime();

        if (now -
                lastRightClickTime <
                RIGHT_CLICK_DEBOUNCE_MS) {

            writeLog(
                    "Duplicate right-click ignored"
            );

            return true;
        }

        lastRightClickTime = now;

        writeLog(
                "RIGHT detected in " +
                        origin
        );

        showControlMenu();

        return true;
    }

    @Override
    public boolean dispatchTouchEvent(
            MotionEvent event) {

        logMotionEvent(
                "TOUCH",
                event
        );

        if (handleRightClick(
                event,
                "TOUCH")) {

            return true;
        }

        return super.dispatchTouchEvent(
                event
        );
    }

    @Override
    public boolean dispatchGenericMotionEvent(
            MotionEvent event) {

        logMotionEvent(
                "GENERIC",
                event
        );

        if (handleRightClick(
                event,
                "GENERIC")) {

            return true;
        }

        return super
                .dispatchGenericMotionEvent(
                        event
                );
    }

    // ------------------------------------------------------------
    // Keyboard / EO1 touch keys
    // ------------------------------------------------------------

    @Override
    public boolean onKeyDown(
            int keyCode,
            KeyEvent event) {

        /*
         * EO1 top touch keys can arrive
         * in large bursts.
         */
        if (keyCode == 132 ||
                keyCode == 134) {

            return true;
        }

        writeLog(
                "KEY keyCode=" +
                        keyCode +
                        " repeat=" +
                        event.getRepeatCount()
        );

        // Space = Next
        if (keyCode ==
                KeyEvent.KEYCODE_SPACE) {

            if (currentMode == MODE_LOCAL) {
                showNextMedia();
            } else if (currentMode == MODE_ART) {
                showNextArt();
            }

            return true;
        }

        // M = menu
        if (keyCode ==
                KeyEvent.KEYCODE_M) {

            showControlMenu();

            return true;
        }

        // L = Local Gallery
        if (keyCode ==
                KeyEvent.KEYCODE_L) {

            showLocalMode();

            return true;
        }

        /*
         * P retained for compatibility:
         * P = Network Gallery.
         */
        if (keyCode ==
                KeyEvent.KEYCODE_P) {

            showNetworkMode();

            return true;
        }

        // R = Rescan
        if (keyCode ==
                KeyEvent.KEYCODE_R) {

            if (currentMode ==
                    MODE_LOCAL) {

                loadMediaList();

                mediaIndex = -1;

                showNextMedia();

                Toast.makeText(
                        this,
                        "Media rescanned",
                        Toast.LENGTH_SHORT
                ).show();
            }

            return true;
        }

        return super.onKeyDown(
                keyCode,
                event
        );
    }

    // ------------------------------------------------------------
    // Diagnostic logging
    // ------------------------------------------------------------

    private void startNewLog() {

        File logFile =
                new File(LOG_FILE);

        File parent =
                logFile.getParentFile();

        if (parent != null &&
                !parent.exists()) {

            parent.mkdirs();
        }

        try {

            FileWriter writer =
                    new FileWriter(
                            logFile,
                            false
                    );

            writer.write(
                    "EO1 v0.4 diagnostic log\n"
            );

            writer.write(
                    "=======================\n"
            );

            writer.close();

        } catch (IOException ignored) {
        }
    }

    private synchronized void writeLog(
            String message) {

        try {

            FileWriter writer =
                    new FileWriter(
                            LOG_FILE,
                            true
                    );

            SimpleDateFormat sdf =
                    new SimpleDateFormat(
                            "HH:mm:ss.SSS",
                            Locale.US
                    );

            writer.write(
                    sdf.format(
                            new Date()
                    ) +
                            " " +
                            message +
                            "\n"
            );

            writer.close();

        } catch (IOException ignored) {
        }
    }

    private void logMotionEvent(
            String type,
            MotionEvent event) {

        int action =
                event.getAction();

        int actionMasked =
                event.getActionMasked();

        int source =
                event.getSource();

        int buttons =
                event.getButtonState();

        boolean mouse =
                isMouseEvent(event);

        boolean secondary =
                isRightButton(event);

        writeLog(
                type +
                        " action=" +
                        action +
                        " actionMasked=" +
                        actionMasked +
                        " actionName=" +
                        MotionEvent
                                .actionToString(
                                        actionMasked
                                ) +
                        " source=0x" +
                        Integer.toHexString(
                                source
                        ) +
                        " sourceMouse=" +
                        mouse +
                        " buttonState=0x" +
                        Integer.toHexString(
                                buttons
                        ) +
                        " secondary=" +
                        secondary +
                        " x=" +
                        event.getX() +
                        " y=" +
                        event.getY()
        );
    }
}