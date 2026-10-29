package com.dan.eo1;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.DialogInterface;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.os.Handler;
import android.os.SystemClock;
import android.view.KeyEvent;
import android.view.MotionEvent;
import android.view.View;
import android.view.ViewGroup;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ArrayAdapter;
import android.widget.ImageView;
import android.widget.ProgressBar;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.VideoView;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Date;
import java.util.List;
import java.util.Locale;

public class MainActivity extends Activity {

    // ------------------------------------------------------------
    // Basic settings
    // ------------------------------------------------------------

    private static final String MEDIA_DIR =
            "/sdcard/EO1-Museum/images";

    private static final String LOG_FILE =
            "/sdcard/EO1-Museum/mouse_log.txt";

    // PC running: python -m http.server 8000
    private static final String PC_GALLERY_URL =
            "http://192.168.1.103:8000/";

    private static final long IMAGE_INTERVAL = 15000L;
    private static final long CROSSFADE_DURATION = 2000L;

    private static final int MODE_LOCAL = 0;
    private static final int MODE_PC = 1;

    // One physical right-click can arrive through more than one
    // MotionEvent path on this Android 4.4 device.
    private static final long RIGHT_CLICK_DEBOUNCE_MS = 400L;

    // ------------------------------------------------------------
    // Views
    // ------------------------------------------------------------

    private ImageView imageView;
    private ImageView imageViewNext;
    private VideoView videoView;
    private WebView webView;
    private ProgressBar progressBar;
    private TextView clockView;

    // ------------------------------------------------------------
    // Media
    // ------------------------------------------------------------

    private final List<File> mediaFiles =
            new ArrayList<File>();

    private int mediaIndex = -1;

    private final Handler handler = new Handler();

    private final Runnable nextImageRunnable =
            new Runnable() {
                @Override
                public void run() {
                    writeLog("TIMER showNextMedia()");
                    showNextMedia();
                }
            };

    // ------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------

    private boolean clockVisible = false;

    private final Handler clockHandler = new Handler();

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

                    /*
                     * Update shortly after the next minute boundary.
                     * No need to wake up every second because seconds
                     * are not displayed.
                     */
                    long now = System.currentTimeMillis();
                    long delay =
                            60000L - (now % 60000L) + 100L;

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
     * PC Gallery is session-only and is never remembered.
     */
    private int currentMode = MODE_LOCAL;

    /*
     * true  = imageView currently contains the visible image
     * false = imageViewNext currently contains the visible image
     */
    private boolean firstImageActive = true;

    /*
     * False until the first image has actually been displayed.
     * The first image appears immediately; cross-fade begins
     * with the second image.
     */
    private boolean hasCurrentImage = false;

    private long lastRightClickTime = 0L;

    private AlertDialog controlDialog;

    // ------------------------------------------------------------
    // Activity lifecycle
    // ------------------------------------------------------------

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        imageView =
                (ImageView) findViewById(R.id.imageView);

        imageViewNext =
                (ImageView) findViewById(R.id.imageViewNext);

        videoView =
                (VideoView) findViewById(R.id.videoView);

        webView =
                (WebView) findViewById(R.id.webView);

        progressBar =
                (ProgressBar) findViewById(R.id.progressBar);

        clockView =
                (TextView) findViewById(R.id.clockView);

        startNewLog();
        writeLog("onCreate");

        setupWebView();
        setupVideoView();

        /*
         * Always start in Local Gallery.
         * No SharedPreferences mode restoration.
         */
        currentMode = MODE_LOCAL;
        clockVisible = true;
        clockView.setVisibility(View.VISIBLE);
        clockView.bringToFront();
        clockHandler.post(clockRunnable);

        showLocalMode();
    }

    @Override
    protected void onResume() {
        super.onResume();

        writeLog("onResume");

        if (currentMode == MODE_LOCAL &&
                videoView.getVisibility() == View.VISIBLE &&
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

        clockHandler.removeCallbacks(
                clockRunnable
        );

        if (videoView != null) {
            videoView.stopPlayback();
        }

        if (controlDialog != null) {
            controlDialog.dismiss();
            controlDialog = null;
        }

        super.onDestroy();
    }

    // ------------------------------------------------------------
    // WebView
    // ------------------------------------------------------------

    private void setupWebView() {

        webView.setBackgroundColor(Color.BLACK);

        webView.getSettings()
                .setJavaScriptEnabled(true);

        webView.setWebViewClient(
                new WebViewClient()
        );
    }

    // ------------------------------------------------------------
    // VideoView
    // ------------------------------------------------------------

    private void setupVideoView() {

        videoView.setOnPreparedListener(mp -> {

            writeLog("Video prepared");

            hideProgress();

            try {

                videoView.start();

                writeLog("Video started");

            } catch (Exception e) {

                writeLog(
                        "Video start error: " +
                                e.getMessage()
                );

                hideProgress();

                showNextMedia();
            }
        });

        videoView.setOnCompletionListener(mp -> {

            writeLog("Video completed");

            hideProgress();

            showNextMedia();
        });

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
                                    showNextMedia();
                                }
                            },
                            500
                    );

                    return true;
                });
    }

    // ------------------------------------------------------------
    // Local Gallery mode
    // ------------------------------------------------------------

    private void showLocalMode() {

        writeLog("showLocalMode");

        currentMode = MODE_LOCAL;

        handler.removeCallbacks(
                nextImageRunnable
        );

        hideProgress();

        webView.stopLoading();
        webView.setVisibility(View.GONE);

        try {
            videoView.stopPlayback();
        } catch (Exception ignored) {
        }

        videoView.setVisibility(View.GONE);

        /*
         * Reset image layers when entering Local Gallery.
         * This makes the first local image appear immediately.
         */
        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setAlpha(1f);
        imageViewNext.setAlpha(0f);

        imageView.setVisibility(View.INVISIBLE);
        imageViewNext.setVisibility(View.INVISIBLE);

        firstImageActive = true;
        hasCurrentImage = false;

        loadMediaList();

        if (mediaFiles.isEmpty()) {

            imageView.setVisibility(View.GONE);
            imageViewNext.setVisibility(View.GONE);

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
                    "Media directory listFiles() returned null"
            );

            return;
        }

        for (File file : files) {

            if (!file.isFile()) {
                continue;
            }

            String name =
                    file.getName()
                            .toLowerCase(Locale.US);

            if (name.endsWith(".jpg") ||
                    name.endsWith(".jpeg") ||
                    name.endsWith(".png") ||
                    name.endsWith(".mp4")) {

                mediaFiles.add(file);
            }
        }

        Collections.shuffle(mediaFiles);

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
                    "showNextMedia: media list empty"
            );

            loadMediaList();

            if (mediaFiles.isEmpty()) {
                return;
            }
        }

        mediaIndex++;

        if (mediaIndex >= mediaFiles.size()) {

            Collections.shuffle(mediaFiles);

            mediaIndex = 0;

            writeLog(
                    "Media list reshuffled"
            );
        }

        File file =
                mediaFiles.get(mediaIndex);

        writeLog(
                "Showing media: " +
                        file.getName()
        );

        String name =
                file.getName()
                        .toLowerCase(Locale.US);

        if (name.endsWith(".mp4")) {
            showVideo(file);
        } else {
            showImage(file);
        }
    }

    private void showImage(File file) {

        hideProgress();

        try {
            videoView.stopPlayback();
        } catch (Exception ignored) {
        }

        videoView.setVisibility(View.GONE);
        webView.setVisibility(View.GONE);

        handler.removeCallbacks(
                nextImageRunnable
        );

        /*
         * First image after entering Local Gallery:
         * display immediately, without fading from black.
         */
        if (!hasCurrentImage) {

            imageView.animate().cancel();
            imageViewNext.animate().cancel();

            imageView.setImageURI(null);
            imageView.setImageURI(
                    Uri.fromFile(file)
            );

            imageView.setAlpha(1f);
            imageView.setVisibility(View.VISIBLE);

            imageViewNext.setAlpha(0f);
            imageViewNext.setVisibility(View.INVISIBLE);

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
            newView.setVisibility(View.VISIBLE);

            oldView.setVisibility(View.VISIBLE);
            oldView.setAlpha(1f);

            /*
             * Cross-fade the two image layers.
             */
            newView.animate()
                    .alpha(1f)
                    .setDuration(CROSSFADE_DURATION)
                    .start();

            oldView.animate()
                    .alpha(0f)
                    .setDuration(CROSSFADE_DURATION)
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
                IMAGE_INTERVAL
        );

        writeLog(
                "Image timer scheduled: " +
                        IMAGE_INTERVAL +
                        " ms"
        );
    }

    private void showVideo(File file) {

        handler.removeCallbacks(
                nextImageRunnable
        );

        /*
         * Hide both image layers.
         * The next image after a video will start cleanly.
         */
        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setVisibility(View.GONE);
        imageViewNext.setVisibility(View.GONE);

        hasCurrentImage = false;
        firstImageActive = true;

        videoView.setVisibility(View.VISIBLE);

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
    // PC Gallery mode
    // ------------------------------------------------------------

    private void showWebMode() {

        writeLog("showWebMode");

        currentMode = MODE_PC;

        handler.removeCallbacks(
                nextImageRunnable
        );

        hideProgress();

        try {
            videoView.stopPlayback();
        } catch (Exception ignored) {
        }

        imageView.animate().cancel();
        imageViewNext.animate().cancel();

        imageView.setVisibility(View.GONE);
        imageViewNext.setVisibility(View.GONE);
        videoView.setVisibility(View.GONE);

        hasCurrentImage = false;
        firstImageActive = true;

        webView.setVisibility(View.VISIBLE);

        webView.loadUrl(
                PC_GALLERY_URL
        );
    }

    // ------------------------------------------------------------
    // Clock
    // ------------------------------------------------------------

    private void toggleClock() {

        clockVisible = !clockVisible;

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

            writeLog("Clock ON");

        } else {

            clockHandler.removeCallbacks(
                    clockRunnable
            );

            clockView.setVisibility(
                    View.GONE
            );

            writeLog("Clock OFF");
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

            /*
             * Clock should remain above everything.
             */
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

                currentMode == MODE_PC
                        ? "✓ PC Gallery"
                        : "PC Gallery",

                "Next",
                "Rescan Media",

                clockVisible
                        ? "Clock: Off"
                        : "Clock: On"
        };

        /*
         * Custom adapter:
         * Next and Rescan are disabled only in PC Gallery mode.
         */
        final ArrayAdapter<String> adapter =
                new ArrayAdapter<String>(
                        this,
                        android.R.layout.simple_list_item_1,
                        items
                ) {

                    @Override
                    public boolean isEnabled(int position) {

                        if (currentMode == MODE_PC &&
                                (position == 2 ||
                                        position == 3)) {

                            return false;
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
                                (TextView) view.findViewById(
                                        android.R.id.text1
                                );

                        /*
                         * Alpha alone indicates disabled items.
                         */
                        if (isEnabled(position)) {
                            textView.setAlpha(1.0f);
                        } else {
                            textView.setAlpha(0.45f);
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
                new DialogInterface.OnClickListener() {

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

                                showWebMode();
                                break;

                            case 2:

                                if (currentMode ==
                                        MODE_LOCAL) {

                                    showNextMedia();
                                }

                                break;

                            case 3:

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

                            case 4:

                                toggleClock();
                                break;
                        }
                    }
                }
        );

        builder.setOnDismissListener(
                new DialogInterface.OnDismissListener() {

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
                android.view.InputDevice.SOURCE_MOUSE)
                ==
                android.view.InputDevice.SOURCE_MOUSE;
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
                SystemClock.elapsedRealtime();

        if (now - lastRightClickTime <
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

        return super.dispatchGenericMotionEvent(
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
         * EO1 top touch keys can arrive in large bursts.
         * Ignore them completely and do NOT write them
         * to the diagnostic log.
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

            if (currentMode ==
                    MODE_LOCAL) {

                showNextMedia();
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

        // P = PC Gallery
        if (keyCode ==
                KeyEvent.KEYCODE_P) {

            showWebMode();

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
                    "EO1 v0.3 diagnostic log\n"
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
                    sdf.format(new Date()) +
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
                        MotionEvent.actionToString(
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