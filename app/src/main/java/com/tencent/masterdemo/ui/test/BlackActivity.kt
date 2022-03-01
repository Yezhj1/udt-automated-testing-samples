package com.tencent.masterdemo.ui.test

import android.app.Activity
import android.app.ActionBar
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.WindowManager
import androidx.appcompat.app.AppCompatActivity
import com.tencent.masterdemo.R


class BlackActivity : AppCompatActivity() {
    public override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_black)

        statusBarHide(this)
    }

    /**
     * 设置Activity的statusBar隐藏
     * @param activity
     */
    fun statusBarHide(activity: Activity) {
        // 代表 5.0 及以上
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            val decorView: View = activity.window.decorView
            val option: Int = View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
            decorView.setSystemUiVisibility(option)
            activity.window.statusBarColor = Color.TRANSPARENT
            val actionBar: ActionBar? = activity.actionBar
            actionBar?.hide()
            return
        }

        // versionCode > 4.4  and versionCode < 5.0
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT && Build.VERSION.SDK_INT < Build.VERSION_CODES.LOLLIPOP) {
            activity.window.addFlags(WindowManager.LayoutParams.FLAG_TRANSLUCENT_STATUS)
        }
    }
}