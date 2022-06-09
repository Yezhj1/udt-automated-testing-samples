package com.tencent.masterdemo.ui.notifications

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.ImageView
import android.widget.Toast
import androidx.core.view.marginLeft
import androidx.core.view.setPadding
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import cn.bingoogolapple.bgabanner.BGABanner
import cn.bingoogolapple.bgabanner.BGABannerUtil
import cn.bingoogolapple.bgabanner.BGALocalImageSize
import com.tencent.masterdemo.R


class NotificationsFragment : Fragment() {

    private lateinit var notificationsViewModel: NotificationsViewModel

    override fun onCreateView(
            inflater: LayoutInflater,
            container: ViewGroup?,
            savedInstanceState: Bundle?
    ): View? {
        notificationsViewModel =
                ViewModelProvider(this).get(NotificationsViewModel::class.java)
        val root = inflater.inflate(R.layout.fragment_notifications, container, false)

        val mContentBanner = root.findViewById<BGABanner>(R.id.banner_guide_content)

        val views: MutableList<View> = ArrayList()
        val localImageSize = BGALocalImageSize(720, 1280, 320F, 640F)

        views.add(BGABannerUtil.getItemImageView(context, R.drawable.game1,
            localImageSize, ImageView.ScaleType.CENTER_CROP))
        val err = BGABannerUtil.getItemImageView(context, R.drawable.game2,
        localImageSize, ImageView.ScaleType.FIT_END)
        err.setPadding(100)
        views.add(err)
        views.add(BGABannerUtil.getItemImageView(context, R.drawable.game3,
            localImageSize, ImageView.ScaleType.CENTER_CROP))
        views.add(BGABannerUtil.getItemImageView(context, R.drawable.game4,
            localImageSize, ImageView.ScaleType.CENTER_CROP))
        mContentBanner.setData(views)
        return root
    }
}