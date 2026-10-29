package com.example.metboot;

import android.content.Context;
import android.content.Intent;

final class FirefoxLauncher {
    private static final String FIREFOX_PACKAGE = "org.mozilla.firefox";

    private FirefoxLauncher() {}

    static void launch(Context context) {
        Intent launchIntent =
                context.getPackageManager().getLaunchIntentForPackage(FIREFOX_PACKAGE);

        if (launchIntent != null) {
            launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(launchIntent);
        }
    }
}
