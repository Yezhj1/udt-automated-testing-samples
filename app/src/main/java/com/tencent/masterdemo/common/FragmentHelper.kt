package com.tencent.masterdemo.common

object FragmentHelper {
    const val INDEX_HOME = 0
    const val INDEX_NOTIFICATION = 1
    const val INDEX_DASHBOARD = 2
    const val INDEX_NEW = 3

    var operInterface : OperateInterface? = null
    var operNewsInterface : OperateNewsInterface? = null

    fun switch(id: Int) {
        operInterface?.switchFragment(id)
    }

    fun update(title: String, time: String, showErrorUI: Boolean) {
        operNewsInterface?.updateFragment(title, time, showErrorUI)
    }
}

interface OperateInterface {
    fun switchFragment(id: Int)
}

interface OperateNewsInterface {
    fun updateFragment(title: String, time: String, showErrorUI: Boolean)
}