package com.tencent.wetestdemo;

import android.os.Bundle;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;

public class SelectActivity extends AppCompatActivity {

    public static final String EXTRA_SHOW_INFO = "show_text";

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_select);

        String infoText = getIntent().getStringExtra(EXTRA_SHOW_INFO);
        TextView selectItemsInfo = findViewById(R.id.select_items);
        selectItemsInfo.setText(infoText);
    }
}