package com.tencent.wetestdemo;

import android.app.Activity;
import android.content.Intent;
import android.net.Uri;
import android.os.ParcelFileDescriptor;

import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;

public class TestLoopHelper {

    private static final String ACTION_TEST_LOOP = "com.google.intent.action.TEST_LOOP";
    private static final String EXTRA_SCENARIO = "scenario";

    public static void startTest(Activity activity, Intent launchIntent) {
        if (launchIntent.getAction().equals(ACTION_TEST_LOOP)) {
            int scenario = launchIntent.getIntExtra(EXTRA_SCENARIO, 0);
            Uri logFile = launchIntent.getData();
            String activityName = "activity: " + activity.getLocalClassName();

            appendLog(activity, logFile,
                    activityName + ", start test on scenario: " + scenario);
            appendLog(activity, logFile,
                    activityName + ", loop test on scenario: " + scenario);
            int i = 0;
            while (i++ < 5) {
                try {
                    Thread.sleep(1000);
                } catch (Exception e) {}
                appendLog(activity, logFile,
                        activityName + ", loop " + i + " test on scenario: " + scenario);
            }
            appendLog(activity, logFile,
                    activityName + ", end test on scenario: " + scenario);
            activity.finish();
        }
    }

    private static void appendLog(Activity activity, Uri uri, String msg) {
        try {
            ParcelFileDescriptor pfd = activity.getContentResolver().
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
