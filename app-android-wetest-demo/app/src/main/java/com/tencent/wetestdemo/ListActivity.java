package com.tencent.wetestdemo;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.CheckedTextView;
import android.widget.ListView;

import androidx.appcompat.app.AppCompatActivity;

import java.util.ArrayList;
import java.util.List;

public class ListActivity extends AppCompatActivity {
    private static final List<String> mSelectItems = new ArrayList();

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_list);

        ListView listView = findViewById(R.id.list_item);
        final ArrayList adapterData = new ArrayList();
        for (int i = 0; i < 20; i++) {
            adapterData.add("Item" + i);
        }
        listView.setAdapter(new ArrayAdapter<String>(this,
                android.R.layout.simple_list_item_multiple_choice, adapterData));
        listView.setItemsCanFocus(true);
        listView.setChoiceMode(ListView.CHOICE_MODE_MULTIPLE);
        listView.setOnItemClickListener((parent, view, position, id) -> {
            CheckedTextView item = (CheckedTextView) view;
            String itemName = item.getText().toString();
            if (item.isChecked()) {
                if (!mSelectItems.contains(itemName)) {
                    mSelectItems.add(itemName);
                }
            } else  {
                mSelectItems.remove(itemName);
            }
        });

        Button subBtn = findViewById(R.id.submitbtn);
        subBtn.setOnClickListener(v -> {
            if (mSelectItems.size() == 0) {
                AlertDialog.Builder builder = new AlertDialog.Builder(v.getContext());
                AlertDialog alert = builder
                        .setTitle("Submit Failed")
                        .setMessage("no item selected")
                        .setNeutralButton("ok",
                                (dialog, which) -> dialog.dismiss())
                        .create();
                alert.show();
                return;
            }

            Intent intent = new Intent(getApplicationContext(), SelectActivity.class);
            intent.putExtra(SelectActivity.EXTRA_SHOW_INFO, mSelectItems.toString());
            startActivity(intent);
        });
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        mSelectItems.clear();
    }
}