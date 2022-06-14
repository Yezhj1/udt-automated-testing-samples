# WeA在安卓下设备下的测试demo
使用WeA api点击安卓设备指定的app，并截图

### 设备连接
1.使用 adb 完成手机设备连接

2.使用 **init_driver()** 进行设备连接

```python
init_driver(os_type=OSType.ANDROID, workspace=os.path.dirname(__file__), driver_lib=DriverLib.SCRCPY)
```
###点击app
- 使用 **start_app()** 进行点击操作。
```python
start_app('package name') # 点击指定的app
```
- 截图查看结果

### 测试结果
<img src="..\resource\img\test3.png" width=300>
<img src="..\resource\img\test2.png" width=300>
