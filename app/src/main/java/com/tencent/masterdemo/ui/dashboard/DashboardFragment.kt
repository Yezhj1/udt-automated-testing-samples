package com.tencent.masterdemo.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.afollestad.materialdialogs.MaterialDialog
import com.afollestad.materialdialogs.input.input
import com.tencent.bugly.crashreport.CrashReport
import com.tencent.masterdemo.R

class DashboardFragment : Fragment(),View.OnClickListener {

    private lateinit var dashboardViewModel: NewsViewModel

    override fun onCreateView(
            inflater: LayoutInflater,
            container: ViewGroup?,
            savedInstanceState: Bundle?
    ): View? {
        dashboardViewModel =
                ViewModelProvider(this).get(NewsViewModel::class.java)
        val root = inflater.inflate(R.layout.fragment_dashboard, container, false)
        root.findViewById<TextView>(R.id.submit).setOnClickListener(this)
        root.findViewById<TextView>(R.id.contact).setOnClickListener(this)
        root.findViewById<TextView>(R.id.website).setOnClickListener(this)
        root.findViewById<TextView>(R.id.edit_email).setOnClickListener(this)
        return root
    }

    override fun onClick(view: View) {
        when(view.id) {
            R.id.submit -> {
                System.exit(1)
            }
            R.id.contact -> {
                throw RuntimeException("测试")
            }
            R.id.website -> {
                CrashReport.testANRCrash()
            }
            R.id.edit_email -> {
                activity?.let {
                    MaterialDialog(it).show {
                        input(hintRes = R.string.fragment_dashboard_email_edit_dialog_info)
                        title(R.string.fragment_dashboard_email_edit_dialog_title)
                        negativeButton()
                    }
                }
            }
        }
    }
}