package com.tencent.wetestdemo;

import android.os.AsyncTask;
import android.os.Bundle;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import java.lang.ref.WeakReference;

public class GameLoopActivity extends AppCompatActivity {
    TextView currentScenario;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_gameloop);
        setTitle(R.string.game_loop_name);
        currentScenario = findViewById(R.id.current_scenario);
    }

    @Override
    protected void onResume() {
        super.onResume();
        new RunScenariosTask(this).execute();
    }

    private static class RunScenariosTask extends AsyncTask<Void, Void, Boolean> {
        private final WeakReference<GameLoopActivity> activity;

        RunScenariosTask(GameLoopActivity activity) {
            this.activity = new WeakReference<>(activity);
        }

        @Override
        protected void onPreExecute() {
            super.onPreExecute();
            if (activity.get() != null) {
                activity.get().currentScenario.setText(activity.get().getString(
                        R.string.current_scenario,
                        TestLoopHelper.getScenario(activity.get().getIntent())));
            }
        }

        @Override
        protected Boolean doInBackground(Void... params) {
            if (activity.get() == null) {
                return false;
            }
            return TestLoopHelper.startTest(activity.get().getApplicationContext(),
                    activity.get().getIntent());
        }

        @Override
        protected void onPostExecute(Boolean finishedAll) {
            if (finishedAll) {
                if (activity.get() != null) {
                    activity.get().finish();
                }
            }
        }
    }
}