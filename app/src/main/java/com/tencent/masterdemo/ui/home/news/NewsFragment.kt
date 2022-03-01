package com.tencent.masterdemo.ui.dashboard

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.fragment.app.Fragment
import androidx.lifecycle.Observer
import androidx.lifecycle.ViewModelProvider
import com.tencent.masterdemo.FragmentHelper
import com.tencent.masterdemo.OperateNewsInterface
import com.tencent.masterdemo.R

class NewsFragment : Fragment(), OperateNewsInterface {

    private lateinit var dashboardViewModel: NewsViewModel
    private lateinit var newsTitle :TextView
    private lateinit var newsTime :TextView
    private lateinit var errorUI :TextView

    override fun onCreateView(
            inflater: LayoutInflater,
            container: ViewGroup?,
            savedInstanceState: Bundle?
    ): View? {
        dashboardViewModel =
                ViewModelProvider(this).get(NewsViewModel::class.java)
        val root = inflater.inflate(R.layout.fragment_news, container, false)
        newsTitle = root.findViewById(R.id.news_title)
        newsTime = root.findViewById(R.id.news_time)
        errorUI = root.findViewById(R.id.content1)

        FragmentHelper.operNewsInterface = this
        return root
    }

    override fun updateFragment(title: String, time: String, showErrorUI: Boolean) {
        newsTitle.text = title
        newsTime.text = time

        if (showErrorUI) {
            errorUI.visibility = View.VISIBLE
        } else {
            errorUI.visibility = View.GONE
        }
    }
}