package com.tencent.wetestdemo;

import android.app.AlertDialog;
import android.content.Intent;
import android.content.res.Resources;
import android.os.Bundle;
import android.text.TextUtils;
import androidx.appcompat.app.AppCompatActivity;
import android.widget.Button;
import android.widget.EditText;

public class LoginActivity extends AppCompatActivity {

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_login);
        setTitle(R.string.login_name);

        final EditText usernameEditText = findViewById(R.id.username);
        final EditText passwordEditText = findViewById(R.id.password);
        final Button loginButton = findViewById(R.id.login);
        loginButton.setOnClickListener(v -> {
            if (TextUtils.isEmpty(usernameEditText.getText().toString())
                    || TextUtils.isEmpty(passwordEditText.getText().toString())) {
                AlertDialog.Builder builder = new AlertDialog.Builder(this);
                AlertDialog alert = builder
                        .setTitle("Login Failed")
                        .setMessage("username or password error")
                        .setNeutralButton("ok",
                                (dialog, which) -> dialog.dismiss())
                        .create();
                alert.show();
            } else {
                startActivity(new Intent(getApplicationContext(), ListActivity.class));
            }
        });
    }
}