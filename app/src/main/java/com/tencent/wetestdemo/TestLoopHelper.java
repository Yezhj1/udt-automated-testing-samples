package com.tencent.wetestdemo;

import android.app.Activity;
import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.util.Log;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;

public class TestLoopHelper {
    private static final String TAG = "TestLoopHelper";

    private static final String ACTION_TEST_LOOP = "com.google.intent.action.TEST_LOOP";
    private static final String EXTRA_SCENARIO = "scenario";

    public static int getScenario(Intent launchIntent) {
        if (launchIntent.getAction().equals(ACTION_TEST_LOOP)) {
            return launchIntent.getIntExtra(EXTRA_SCENARIO, 0);
        }
        return -1;
    }

    public static boolean startTest(Context context, Intent launchIntent) {
        int scenario = getScenario(launchIntent);
        if (scenario < 0) {
            return false;
        }

        Uri logFile = launchIntent.getData();
        String activityName = "activity: " + context.getPackageName();

        appendLog(context, logFile,
                activityName + ", start test on scenario: " + scenario);
        appendLog(context, logFile,
                activityName + ", loop test on scenario: " + scenario);
        int i = 0;
        while (i++ < 10) {
            try {
                Thread.sleep(1000);
            } catch (Exception e) {
            }
            appendLog(context, logFile,
                    activityName + ", loop " + i + " test on scenario: " + scenario);
        }
        appendLog(context, logFile,
                activityName + ", end test on scenario: " + scenario);
        return true;
    }

    private static void appendLog(Context context, Uri uri, String msg) {
        Log.i(TAG, "appendLog: " + msg);
        try {
            ParcelFileDescriptor pfd = context.getContentResolver().
                    openFileDescriptor(uri, "wa");
            FileOutputStream fileOutputStream =
                    new FileOutputStream(pfd.getFileDescriptor());
            fileOutputStream.write((msg + "\n").getBytes());
            // Let the document provider know you're done by closing the stream.
            fileOutputStream.close();
            pfd.close();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        } catch (IOException e) {
            e.printStackTrace();
        }
    }
}
