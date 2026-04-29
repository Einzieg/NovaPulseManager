# Bugfix: “新增设备”弹窗输入框无法聚焦（Electron）

## 问题现象

- 仅在 Electron 桌面端出现：打开“新增设备”弹窗后，设备名输入框点击无光标、无法聚焦，导致无法输入。
- 同页面其它输入（例如设备页顶部搜索框）正常。

相关组件：[`DeviceCreateModal()`](frontend/src/components/devices/DeviceCreateModal.tsx:12)

## 处理方式

在弹窗挂载后，主动将焦点设置到设备名输入框：

- 使用 `ref` 持有输入框
- `useEffect` 中 `setTimeout(0)` 延迟一帧执行 `focus({ preventScroll: true })`

实现位置：[`DeviceCreateModal()`](frontend/src/components/devices/DeviceCreateModal.tsx:12)

## 回归验证

- Electron 桌面端：打开“新增设备”弹窗，设备名输入框应自动出现光标并可输入；鼠标点击也可正常聚焦。
- 浏览器端：同样验证“新增设备”弹窗输入框可聚焦与输入。
- 其它输入面板（例如工作流节点配置面板）不受影响：[`NodeConfigPanel`](frontend/src/components/workflow/NodeConfigPanel.tsx:13)

