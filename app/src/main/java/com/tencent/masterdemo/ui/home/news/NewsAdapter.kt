package com.tencent.masterdemo.ui.home.news

import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.RecyclerView
import com.tencent.masterdemo.R
import com.tencent.masterdemo.ui.home.HomeViewModel

class NewsAdapter(context: Context) :
        RecyclerView.Adapter<NewsAdapter.CheckItemViewHolder>(),
        View.OnClickListener {

    inner class CheckItemViewHolder(itemView: View) : RecyclerView.ViewHolder(itemView) {
        val checkItemTitleTextView: TextView = itemView.findViewById(R.id.tv_new_title)
        val checkItemSubTextView: TextView = itemView.findViewById(R.id.tv_new_time)
    }

    private val context = context
    private val inflater: LayoutInflater = LayoutInflater.from(context)
    private var model: HomeViewModel? = null

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): CheckItemViewHolder {
        val itemView = inflater.inflate(R.layout.news_item, parent, false)
        return CheckItemViewHolder(itemView)
    }

    override fun onBindViewHolder(holder: CheckItemViewHolder, position: Int) {
        val current = model?.getItemList(context)?.get(position)
        if (current != null) {
            holder.itemView.setOnClickListener(this)
            holder.checkItemTitleTextView.text = current.title
            holder.checkItemSubTextView.text = current.time
        }
    }

    override fun getItemCount(): Int {
        return model!!.getItemList(context).size
    }

    override fun onClick(v: View?) {
        if (v != null) {
            val holder = CheckItemViewHolder(v)
            model?.onViewClick(context, holder.checkItemTitleTextView.text as String)
        }
    }

    fun setModel(model: HomeViewModel?) {
        this.model = model
        notifyDataSetChanged()
    }
}