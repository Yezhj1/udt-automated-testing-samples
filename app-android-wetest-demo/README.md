# WeA在安卓身背下的测试demo
使用WeA api对安卓设备做简单的操作，包括点击和截取当前手机页面

### 设备连接
1.使用 adb 完成手机设备连接

2.使用 **init_driver()** 进行设备连接

```python
init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), driver_lib=DriverLib.SCRCPY)
```
### 操作设备
1.点击操作和截图操作
- 使用 **click()** 进行点击操作。 **click()** 支持多方式点击操作，这里展示的是其中的一种--点击坐标
```python
click([200, 200]) # 点击左面上的[200, 200]位置
```
- **get_img()** 获取当前屏幕截图，并借助opencv中的 **imread()** 函数完成图片输出

2.**stop_driver()** 在脚本运行结束后调用，释放相关驱动，并生成报告

### 测试结果
<div align=left>
<img src="..\resource\img\test1.png" width=300>



