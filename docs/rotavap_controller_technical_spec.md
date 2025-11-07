# 旋转蒸发仪控制器技术规格文档

**版本**: 1.0
**更新日期**: 2025-11-07
**适用设备**: RotavapController (rotavap_device.py)

---

## 目录

1. [系统概述](#1-系统概述)
2. [通信架构](#2-通信架构)
3. [命令集](#3-命令集)
4. [设备状态](#4-设备状态)
5. [超时配置](#5-超时配置)
6. [校准参数](#6-校准参数)
7. [PLC 寄存器映射](#7-plc-寄存器映射)
8. [错误处理](#8-错误处理)
9. [使用示例](#9-使用示例)
10. [常见问题](#10-常见问题)

---

## 1. 系统概述

### 1.1 功能描述

旋转蒸发仪控制器提供完整的设备控制接口，支持以下功能：

- **加热控制**: 设定温度和开关控制
- **冷却控制**: 设定温度和开关控制
- **真空控制**: 真空度设定、真空阀/充气阀控制
- **旋转控制**: 转速设定和开关控制
- **升降控制**: 升降位置设定
- **自动高度调节**: 根据烧瓶体积自动设置高度
- **废液处理**: 自动排放废液
- **真空阈值监控**: 自动控制真空度到目标值

### 1.2 通信方式

- **API 通信**: HTTP REST API (`/api/v1/info`, `/api/v1/process`)
- **PLC 通信**: Modbus 协议（用于高度控制和废液控制）

### 1.3 工作模式

- **实际模式 (mock=False)**: 连接真实设备
- **Mock 模式 (mock=True)**: 模拟模式，用于测试和开发

---

## 2. 通信架构

### 2.1 API 端点

| 端点 | 方法 | 功能 | 返回数据 |
|------|------|------|----------|
| `/api/v1/info` | GET | 获取设备信息 | 设备基本信息 |
| `/api/v1/process` | GET | 获取工艺过程状态 | 当前运行状态和参数 |
| `/api/v1/process` | PUT | 更改设备参数 | 操作结果 |

### 2.2 PLC 通信

通过 Modbus 协议与 PLC 通信，用于：
- 高度自动调节
- 废液排放控制
- 完成状态读取

---

## 3. 命令集

### 3.1 API 通信命令

#### 3.1.1 获取设备信息

```python
def get_info() -> Dict[str, Any]
```

**功能**: 获取设备基本信息
**参数**: 无
**返回**: 设备信息字典
**异常**: 连接失败时抛出异常

---

#### 3.1.2 获取工艺过程状态

```python
def get_process() -> Dict[str, Any]
```

**功能**: 获取当前工艺过程的实时状态
**参数**: 无
**返回**: 包含以下字段的字典：
- `globalStatus`: 全局状态（running）
- `vacuum`: 真空状态（set, act）
- `heating`: 加热状态（set, act, running）
- `cooling`: 冷却状态（set, act, running）
- `rotation`: 旋转状态（set, act, running）
- `lift`: 升降状态（set）

**异常**: 连接失败时抛出异常

---

#### 3.1.3 获取结构化设备状态

```python
def get_device_status() -> DeviceStatus
```

**功能**: 获取格式化的设备状态对象
**参数**: 无
**返回**: DeviceStatus 对象
- `running`: bool - 是否运行中
- `vacuum_actual`: float - 当前真空度 (mbar)
- `heating_actual`: float - 当前加热温度 (°C)
- `cooling_actual`: float - 当前冷却温度 (°C)
- `rotation_actual`: float - 当前转速 (rpm)

---

#### 3.1.4 更改设备参数

```python
def change_device_parameters(
    heating: Optional[HeatingConfig] = None,
    cooling: Optional[CoolingConfig] = None,
    vacuum: Optional[VacuumConfig] = None,
    rotation: Optional[RotationConfig] = None,
    lift: Optional[LiftConfig] = None,
    running: Optional[bool] = None,
    program: Optional[ProgramConfig] = None
) -> Dict[str, Any]
```

**功能**: 统一的设备参数设置接口
**参数**: 所有参数均为可选，仅设置提供的参数
**返回**: 服务器响应字典
**异常**: 参数错误或连接失败时抛出异常

---

### 3.2 蒸发过程控制

#### 3.2.1 启动蒸发

```python
def run_evaporation(delay: int = 10) -> Dict[str, Any]
```

**功能**: 启动蒸发过程
**参数**:
- `delay`: 启动后延迟时间（秒），默认 10 秒
**返回**: 服务器响应
**说明**: 启动后会自动延迟指定时间，等待系统稳定

---

#### 3.2.2 停止蒸发

```python
def stop_evaporation() -> Dict[str, Any]
```

**功能**: 停止蒸发过程
**参数**: 无
**返回**: 服务器响应

---

#### 3.2.3 同步等待蒸发完成

```python
def xuanzheng_sync(
    timeout_min: int = 120,
    poll_interval: int = 2
) -> bool
```

**功能**: 同步等待蒸发过程自然完成（未运行 → 运行中 → 完成）
**参数**:
- `timeout_min`: 超时时间（分钟），默认 120 分钟
- `poll_interval`: 状态轮询间隔（秒），默认 2 秒
**返回**:
- `True`: 成功完成
- `False`: 超时或异常
**状态机逻辑**:
```
初始状态 → 检测到运行 → 检测到停止 → 返回成功
                ↓ 超时
            停止蒸发 → 返回失败
```

---

### 3.3 高度控制

#### 3.3.1 设置高度

```python
def set_height(volume: int) -> None
```

**功能**: 根据烧瓶体积自动设置升降高度
**参数**:
- `volume`: 烧瓶体积（ml），支持：1000, 500, 100, 50, 0
**异常**:
- `ValueError`: 不支持的体积值
- `TimeoutError`: 高度设置超时（默认 120 秒）

**执行流程**:
1. 验证体积值
2. 写入 PLC 高度寄存器
3. 设置烧瓶尺寸参数（volume > 0 时）
4. 启动自动设置（AUTO_SET）
5. 等待完成标志（AUTO_FINISH）
6. 复位自动设置标志

---

### 3.4 真空控制

#### 3.4.1 启动真空泵

```python
def run_vacuum() -> Dict[str, Any]
```

**功能**: 启动真空泵，打开真空阀
**参数**: 无
**默认设置**:
- 真空度设定: 150 mbar
- 真空阀: 打开
- 充气阀: 关闭
- 升降位置: 0

---

#### 3.4.2 停止真空泵

```python
def stop_vacuum() -> Dict[str, Any]
```

**功能**: 停止真空泵，关闭真空阀
**参数**: 无

---

#### 3.4.3 打开排气阀

```python
def drain_valve_open(duration: int = 5) -> Dict[str, Any]
```

**功能**: 打开充气阀，用于泄压
**参数**:
- `duration`: 持续时间（秒），默认 5 秒
**说明**: 会自动阻塞指定时间后返回

---

#### 3.4.4 抽真空至目标值

```python
def vacuum_until_below_threshold(
    threshold: float = 400,
    poll_interval: int = 1
) -> bool
```

**功能**: 自动抽真空直到低于目标阈值
**参数**:
- `threshold`: 目标真空度（mbar），默认 400
- `poll_interval`: 轮询间隔（秒），默认 1
**返回**:
- `True`: 成功达到目标
- `False`: 发生错误
**说明**:
- 会自动启动真空泵
- 达到阈值后自动停止真空泵
- Mock 模式下立即返回成功

---

#### 3.4.5 排气至目标值

```python
def drain_until_above_threshold(
    threshold: float = 900,
    poll_interval: int = 1,
    wait_after: int = 5
) -> bool
```

**功能**: 自动排气直到高于目标阈值
**参数**:
- `threshold`: 目标真空度（mbar），默认 900
- `poll_interval`: 轮询间隔（秒），默认 1
- `wait_after`: 达到阈值后等待时间（秒），默认 5
**返回**:
- `True`: 成功达到目标
- `False`: 发生错误

---

### 3.5 废液控制

#### 3.5.1 启动废液排放

```python
def start_waste_liquid(
    wait_for_completion: bool = False,
    timeout: int = 60
) -> bool
```

**功能**: 启动废液排放系统
**参数**:
- `wait_for_completion`: 是否等待排放完成，默认 False
- `timeout`: 等待超时时间（秒），默认 60
**返回**:
- `True`: 启动成功（或完成）
- `False`: 启动失败
**执行流程**:
1. 发送脉冲信号到 PLC（True → False）
2. 延迟 2 秒
3. 如果 wait_for_completion=True，则等待完成标志

---

### 3.6 连接管理

#### 3.6.1 关闭连接

```python
def close() -> None
```

**功能**: 关闭 API 连接
**参数**: 无
**说明**: 使用上下文管理器时会自动调用

---

## 4. 设备状态

### 4.1 设备状态数据结构

```python
@dataclass
class DeviceStatus:
    running: bool = False              # 是否运行中
    vacuum_actual: float = 0.0         # 当前真空度 (mbar)
    heating_actual: float = 0.0        # 当前加热温度 (°C)
    cooling_actual: float = 0.0        # 当前冷却温度 (°C)
    rotation_actual: float = 0.0       # 当前转速 (rpm)
```

### 4.2 状态读取方法

| 方法 | 返回类型 | 更新频率 | 说明 |
|------|----------|----------|------|
| `get_process()` | Dict | 实时 | 原始 API 响应 |
| `get_device_status()` | DeviceStatus | 实时 | 结构化状态对象 |

### 4.3 运行状态定义

| 状态 | 值 | 说明 |
|------|-----|------|
| 未运行 | running=False | 设备停止状态 |
| 运行中 | running=True | 设备正在执行蒸发过程 |

---

## 5. 超时配置

### 5.1 超时参数表

| 操作 | 参数名 | 默认值 | 可配置 | 说明 |
|------|--------|--------|--------|------|
| 同步等待蒸发完成 | `timeout_min` | 120 分钟 | ✓ | `xuanzheng_sync()` |
| 高度设置 | `timeout` | 120 秒 | ✗ | `_wait_height_finish()` 内部 |
| 废液排放 | `timeout` | 60 秒 | ✓ | `start_waste_liquid()` |
| 状态轮询间隔 | `poll_interval` | 2 秒 | ✓ | `xuanzheng_sync()` |
| 真空控制轮询 | `poll_interval` | 1 秒 | ✓ | `vacuum_until_below_threshold()` |

### 5.2 类级别默认常量

```python
DEFAULT_VACUUM_SET = 150        # 默认真空设定值 (mbar)
DEFAULT_LIFT_SET = 0            # 默认升降位置
DEFAULT_POLL_INTERVAL = 2       # 默认轮询间隔（秒）
DEFAULT_SYNC_TIMEOUT = 120      # 默认同步超时（分钟）
```

### 5.3 超时处理逻辑

所有异步等待操作都采用统一的超时处理模式：

```python
start_time = time.time()
while True:
    if time.time() - start_time > timeout:
        logger.error(f"操作超时")
        raise TimeoutError(...)

    # 检查完成条件
    if done:
        return True

    time.sleep(poll_interval)
```

---

## 6. 校准参数

### 6.1 体积-高度映射表

| 烧瓶体积 (ml) | PLC 高度值 | 烧瓶尺寸 | 说明 |
|---------------|------------|----------|------|
| 1000 | 1050 | LARGE (2) | 1000ml 大烧瓶 |
| 500 | 1150 | SMALL (1) | 500ml 小烧瓶 |
| 100 | 1400 | SMALL (1) | 100ml 小烧瓶 |
| 50 | 1417 | SMALL (1) | 50ml 小烧瓶 |
| 0 | 0 | SMALL (1) | 归零位置 |

### 6.2 烧瓶尺寸枚举

```python
class FlaskSize(IntEnum):
    SMALL = 1   # 小烧瓶（50ml, 100ml, 500ml）
    LARGE = 2   # 大烧瓶（1000ml）
```

### 6.3 程序类型

```python
class ProgramType(str, Enum):
    AUTO_DEST = "AutoDest"  # 自动蒸馏程序
```

### 6.4 校准修改方法

**问题**: 代码中的体积-高度映射是硬编码的，如何修改校准参数？

**当前方案**: 修改 `VOLUME_HEIGHT_MAP` 字典
```python
VOLUME_HEIGHT_MAP = {
    1000: (VolumeHeight.VOLUME_1000ML, FlaskSize.LARGE),
    500: (VolumeHeight.VOLUME_500ML, FlaskSize.SMALL),
    # ...
}
```

**建议**: 是否需要添加动态校准接口？例如：
```python
def set_volume_calibration(volume: int, height: int, flask_size: FlaskSize):
    """动态设置体积-高度映射"""
    pass
```

---

## 7. PLC 寄存器映射

### 7.1 寄存器地址表

| 寄存器名称 | 地址 | 类型 | 读/写 | 说明 |
|-----------|------|------|-------|------|
| HEIGHT_ADDRESS | 502 | Holding Register | W | 高度设定值 |
| AUTO_SET | 500 | Coil | W | 自动高度设置启动标志 |
| AUTO_FINISH | 501 | Coil | R | 自动高度设置完成标志 |
| WASTE_LIQUID | 323 | Coil | W | 废液启动标志 |
| WASTE_LIQUID_FINISH | 333 | Coil | R | 废液完成标志 |

### 7.2 PLC 操作类型

| 操作 | Modbus 功能码 | 方法 |
|------|---------------|------|
| 写入单个寄存器 | 0x06 | `plc.write_single_register()` |
| 写入线圈 | 0x05 | `plc.write_coil()` |
| 读取线圈 | 0x01 | `plc.read_coils()` |

### 7.3 PLC 信号时序

#### 高度设置时序图

```
时间轴:  0s    1s    3s          ...          完成
         |     |     |                         |
AUTO_SET: ─┐   └─────┘                        ─
           |         |                         |
         写入      启动等待                  复位标志
         寄存器    自动设置

AUTO_FINISH: ──────────────────────────────┐
                                           └───
                                         完成信号
```

#### 废液启动时序图

```
时间轴:  0s    1s    2s          ...
         |     |     |
WASTE_LIQUID: ─┐
               └─────
             脉冲信号

WASTE_LIQUID_FINISH: ────────────────┐
                                     └───
                                  完成信号
```

---

## 8. 错误处理

### 8.1 异常类型

| 异常 | 触发条件 | 处理方式 |
|------|----------|----------|
| `ValueError` | 不支持的烧瓶体积值 | 立即抛出，提示支持的值 |
| `TimeoutError` | 操作超时 | 记录日志，抛出异常 |
| `ConnectionError` | 网络连接失败 | 记录日志，抛出异常 |
| `json.JSONDecodeError` | API 响应解析失败 | 记录日志，返回空字典 |
| `Exception` | 其他未知错误 | 记录日志，抛出异常 |

### 8.2 异常捕获点

#### 8.2.1 API 通信异常

```python
try:
    response = self.connection.send_request(...)
    return self._parse_response(response)
except Exception as e:
    self.logger.error(f"操作失败: {e}")
    raise
```

**处理**: 记录错误日志并重新抛出异常

#### 8.2.2 JSON 解析异常

```python
try:
    return json.loads(response)
except json.JSONDecodeError as e:
    self.logger.error(f"JSON 解析失败: {e}, 原始数据: {response}")
    return {}
```

**处理**: 记录错误并返回空字典（容错处理）

#### 8.2.3 PLC 读取异常

```python
try:
    done = self.plc.read_coils(self.AUTO_FINISH, 1)[0]
except Exception as e:
    self.logger.warning(f"读取完成状态失败: {e}")
```

**处理**: 记录警告并继续重试

### 8.3 错误恢复机制

#### 8.3.1 超时自动停止

**场景**: `xuanzheng_sync()` 等待超时

**处理**:
```python
if elapsed > timeout:
    self.logger.warning(f"同步等待超时（{timeout_min}分钟），停止蒸发")
    self.stop_evaporation()
    return False
```

#### 8.3.2 真空控制异常恢复

**场景**: `vacuum_until_below_threshold()` 发生异常

**处理**:
```python
except Exception as e:
    self.logger.error(f"抽真空过程出错: {e}")
    self.stop_vacuum()  # 自动停止真空泵
    return False
```

### 8.4 日志记录

日志级别使用规范：

| 级别 | 使用场景 | 示例 |
|------|----------|------|
| DEBUG | 详细调试信息 | 轮询状态、等待完成 |
| INFO | 正常操作流程 | 启动蒸发、设置高度完成 |
| WARNING | 非致命错误 | 读取状态失败（可重试）、空响应 |
| ERROR | 致命错误 | 操作超时、连接失败 |

### 8.5 故障排查指南

**问题**: 代码中缺少明确的故障保护机制和错误恢复流程

**建议补充**:
1. 设备状态自检功能
2. 参数有效性验证
3. 安全联锁逻辑
4. 异常状态自动复位

**需要确认的问题**:
1. PLC 通信失败后是否需要自动重连？
2. 真空泵异常是否需要紧急停机？
3. 高度设置失败是否需要复位到安全位置（0）？
4. 是否需要增加设备自检功能？

---

## 9. 使用示例

### 9.1 基本使用流程

```python
from src.device_control.rotavap_device import RotavapController

# 创建控制器实例
controller = RotavapController(mock=False)

try:
    # 1. 设置高度
    controller.set_height(1000)  # 1000ml 烧瓶

    # 2. 抽真空
    controller.vacuum_until_below_threshold(threshold=400)

    # 3. 启动蒸发
    controller.run_evaporation()

    # 4. 等待完成
    success = controller.xuanzheng_sync(timeout_min=30)

    if success:
        print("蒸发完成")
    else:
        print("蒸发超时")

    # 5. 排气
    controller.drain_until_above_threshold(threshold=900)

    # 6. 废液排放
    controller.start_waste_liquid(wait_for_completion=True)

    # 7. 归零
    controller.set_height(0)

finally:
    controller.close()
```

### 9.2 使用上下文管理器（推荐）

```python
with RotavapController(mock=False) as controller:
    controller.set_height(1000)
    controller.run_evaporation()
    controller.xuanzheng_sync(timeout_min=30)
    controller.set_height(0)
# 自动关闭连接
```

### 9.3 手动参数控制

```python
from src.device_control.rotavap_device import (
    RotavapController, HeatingConfig, VacuumConfig
)

controller = RotavapController(mock=False)

# 设置加热
heating = HeatingConfig(set=60, running=True)
controller.change_device_parameters(heating=heating)

# 设置真空
vacuum = VacuumConfig(set=150, vacuumValveOpen=True)
controller.change_device_parameters(vacuum=vacuum)

# 获取状态
status = controller.get_device_status()
print(f"当前温度: {status.heating_actual}°C")
print(f"当前真空: {status.vacuum_actual}mbar")
```

### 9.4 Mock 模式测试

```python
# 开发测试时使用 Mock 模式
with RotavapController(mock=True) as controller:
    # 所有操作都会被模拟，不会连接真实设备
    controller.set_height(1000)
    controller.vacuum_until_below_threshold()  # 立即返回成功
```

---

## 10. 常见问题

### 10.1 如何修改高度校准参数？

**回答**: 当前需要修改源代码中的 `VOLUME_HEIGHT_MAP` 字典。建议是否添加配置文件或动态校准接口？

### 10.2 真空控制阈值如何选择？

**建议值**:
- 抽真空目标: 300-400 mbar（溶剂蒸发）
- 排气目标: 900-950 mbar（接近常压）

**影响因素**: 溶剂种类、温度、真空泵性能

### 10.3 蒸发过程超时怎么办？

**处理**: `xuanzheng_sync()` 超时后会自动调用 `stop_evaporation()` 停止蒸发，不需要手动干预。

### 10.4 PLC 通信失败如何处理？

**问题**: 代码中缺少 PLC 重连机制

**建议**:
1. 是否需要增加 PLC 连接状态检查？
2. 通信失败后是否自动重试？
3. 多次失败后的降级策略？

### 10.5 如何监控设备实时状态？

```python
import time

controller = RotavapController(mock=False)

while True:
    status = controller.get_device_status()
    print(f"运行: {status.running}, 真空: {status.vacuum_actual}mbar")
    time.sleep(2)
```

### 10.6 是否支持多种程序类型？

**当前**: 仅支持 `AutoDest`（自动蒸馏）
**问题**: 是否需要支持其他程序类型？如手动蒸馏、连续蒸馏等？

---

## 附录 A: 待补充功能

根据代码分析，以下功能在当前版本中缺失，建议补充：

### A.1 故障保护机制

- [ ] 温度超限保护
- [ ] 真空异常保护
- [ ] PLC 通信异常保护
- [ ] 设备自检功能

### A.2 错误恢复

- [ ] PLC 自动重连
- [ ] 操作失败自动复位
- [ ] 紧急停机流程
- [ ] 状态一致性恢复

### A.3 校准管理

- [ ] 动态校准接口
- [ ] 校准参数持久化
- [ ] 校准历史记录
- [ ] 多点校准支持

### A.4 监控增强

- [ ] 实时状态推送
- [ ] 历史数据记录
- [ ] 报警通知机制
- [ ] 性能统计

---

## 附录 B: 配置数据结构

### B.1 加热配置

```python
@dataclass
class HeatingConfig:
    set: float              # 设定温度 (°C)
    running: bool = False   # 是否启动加热
```

### B.2 冷却配置

```python
@dataclass
class CoolingConfig:
    set: float              # 设定温度 (°C)
    running: bool = False   # 是否启动冷却
```

### B.3 真空配置

```python
@dataclass
class VacuumConfig:
    set: float                         # 设定真空度 (mbar)
    vacuumValveOpen: bool = False      # 真空阀状态
    aerateValveOpen: bool = False      # 充气阀状态
    aerateValvePulse: bool = False     # 充气阀脉冲模式
```

### B.4 旋转配置

```python
@dataclass
class RotationConfig:
    set: float              # 设定转速 (rpm)
    running: bool = True    # 是否启动旋转
```

### B.5 升降配置

```python
@dataclass
class LiftConfig:
    set: float              # 设定位置（相对值）
```

### B.6 程序配置

```python
@dataclass
class ProgramConfig:
    type: str = "AutoDest"          # 程序类型
    endVacuum: float = 0            # 结束真空度 (mbar)
    flaskSize: int = 2              # 烧瓶尺寸 (1=小, 2=大)
```

---

## 修订历史

| 版本 | 日期 | 修改内容 | 作者 |
|------|------|----------|------|
| 1.0 | 2025-11-07 | 初始版本，基于 rotavap_device.py | Claude |

---

**文档状态**: 待审核
**待确认问题**: 见附录 A 和各节中的"问题"标注
