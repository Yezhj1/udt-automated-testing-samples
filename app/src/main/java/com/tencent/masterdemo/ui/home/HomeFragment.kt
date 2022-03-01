package com.tencent.masterdemo.ui.home

import android.content.Intent
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import androidx.fragment.app.Fragment
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.tencent.masterdemo.BlackActivity
import com.tencent.masterdemo.R

class HomeFragment : Fragment(), View.OnClickListener {
    private var adapter: NewsAdapter? = null

    private lateinit var homeViewModel: HomeViewModel

    override fun onCreateView(
            inflater: LayoutInflater,
            container: ViewGroup?,
            savedInstanceState: Bundle?
    ): View? {
        val root = inflater.inflate(R.layout.fragment_home, container, false)
        root.findViewById<ImageView>(R.id.banner).setOnClickListener(this)
        return root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        adapter = activity?.let { NewsAdapter(it) }

        val recyclerView: RecyclerView = view.findViewById(R.id.rv_news_list)
        recyclerView.adapter = adapter
        recyclerView.layoutManager = LinearLayoutManager(activity)

        homeViewModel = context?.let { HomeViewModel() }!!
        adapter!!.setModel(homeViewModel)
    }

    override fun onClick(view: View?) {
        when(view?.id) {
            R.id.banner -> {
                startActivity(Intent(context, BlackActivity::class.java))
            }
        }
    }
}