package com.tencent.masterdemo.ui.home

import android.content.Context
import androidx.lifecycle.ViewModel
import com.tencent.masterdemo.R

open class HomeViewModel : ViewModel() {
    private val deviceItem = ArrayList<NewItem>()

    open fun getItemList(context: Context): ArrayList<NewItem> {
        deviceItem.clear()
        deviceItem.add(NewItem(context.getString(R.string.fragment_home_news_item1),
            context.getString(R.string.fragment_home_news_times1)))
        deviceItem.add(NewItem(context.getString(R.string.fragment_home_news_item2),
            context.getString(R.string.fragment_home_news_times2)))
        deviceItem.add(NewItem(context.getString(R.string.fragment_home_news_item3),
            context.getString(R.string.fragment_home_news_times3)))
        deviceItem.add(NewItem(context.getString(R.string.fragment_home_news_item4),
            context.getString(R.string.fragment_home_news_times4)))
        deviceItem.add(NewItem(context.getString(R.string.fragment_home_news_item5),
            context.getString(R.string.fragment_home_news_times5)))
        return deviceItem
    }

    fun onViewClick(title: String) {

    }
}

open class NewItem(var title:String, var time:String)