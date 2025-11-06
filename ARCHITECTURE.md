# System Architecture Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architectural Layers](#architectural-layers)
3. [Communication Protocols](#communication-protocols)
4. [Device Specifications](#device-specifications)
5. [Data Flow](#data-flow)
6. [Security & Safety](#security--safety)
7. [Deployment Architecture](#deployment-architecture)

---

## Overview

The Automated Rotary Evaporator System follows a **layered service-oriented architecture** with clear separation of concerns between user interface, business logic, device control, and hardware communication.

### Design Principles

1. **Modularity**: Each device has independent controllers with standardized interfaces
2. **Asynchrony**: Non-blocking I/O maximizes concurrent hardware utilization
3. **Fault Tolerance**: Graceful degradation and error recovery at all layers
4. **Testability**: Mock mode support throughout the stack
5. **Extensibility**: Plugin architecture for new device types

### Technology Stack

| Layer | Technologies |
|-------|-------------|
| **Presentation** | FastAPI, WebSockets, HTML/JS |
| **Business Logic** | Python 3.11+, asyncio, dataclasses |
| **Device Control** | Object-oriented device abstractions |
| **Communication** | Modbus TCP, HTTP REST, WebSocket, Selenium |
| **Hardware** | PLCs, Socket servers, Web interfaces |
| **Data** | SQLite, Redis, YAML configuration |
| **Monitoring** | Python logging, custom log handlers |

---

## Architectural Layers

### Layer 1: Presentation Layer (`app/`)

**Purpose**: User interfaces and external APIs

```
app/
├── main.py                 # FastAPI application bootstrap
├── api/
│   ├── robot_api.py       # Robot control endpoints
│   └── system_api.py      # System management endpoints
└── middleware/            # Request logging, auth (if needed)
```

**Key Components**:

- **FastAPI Server**: REST API with automatic OpenAPI documentation
- **WebSocket Support**: Real-time status updates to web clients
- **Request Validation**: Pydantic models for type-safe API contracts

**Example Endpoints**:

```python
POST   /api/robot/start          # Start workflow
POST   /api/robot/pause          # Pause execution
POST   /api/robot/resume         # Resume from pause
POST   /api/robot/stop           # Emergency stop
GET    /api/system/status        # Get system state
GET    /api/system/logs          # Stream logs
WS     /ws/status                # Real-time updates
```

---

### Layer 2: Service Layer (`src/service_control/`)

**Purpose**: Business logic and workflow orchestration

```
src/service_control/
├── demo/
│   └── modified_run_lab.py     # Main workflow orchestrator
├── sepu/
│   ├── sepu_service.py         # Chromatography service
│   ├── experiment_graph.py     # GUI for experiment setup
│   └── curve_graph.py          # Real-time curve plotting
└── task_scheduler/
    └── scheduler.py            # Job scheduling (future)
```

**Key Responsibilities**:

1. **Workflow Orchestration**: Coordinate multi-device operations
2. **State Management**: Track experiment progress and handle pause/resume
3. **Error Handling**: Implement retry logic and fallback strategies
4. **Data Processing**: Transform raw device data into meaningful metrics

**Core Classes**:

```python
class ExperimentConfig:
    """Encapsulates all workflow parameters"""
    column_id: int
    wash_time_s: int
    experiment_time_min: int
    # ... other config

class TaskController:
    """Manages workflow execution state"""
    def pause() -> None
    def resume() -> None
    def stop() -> None
    async def wait_if_paused() -> None

async def run_lab(controller, config) -> None:
    """Main workflow execution function"""
```

---

### Layer 3: Device Control Layer (`src/device_control/`)

**Purpose**: Hardware abstraction with unified interfaces

```
src/device_control/
├── robot_control/
│   ├── robot_controller.py     # SCARA robot controller
│   ├── robot_new_control.py    # Alternative robot implementation
│   └── robot_plc.py            # PLC-based robot control
├── sepu/
│   └── api_fun.py              # Chromatography device wrapper
├── opentrons/
│   └── opentrons_device.py     # Opentrons liquid handler
├── xuanzheng_device.py         # Rotary evaporator controller
├── pump_sample.py              # Injection pump
├── peristaltic_pump.py         # Peristaltic pump
├── gear_pump.py                # Gear pump
├── inject_height.py            # Height control via PLC
├── laser_marking.py            # Laser marking system
└── monitor.py                  # Monitoring utilities
```

**Device Interface Pattern**:

All device controllers follow a common pattern:

```python
class DeviceController:
    def __init__(self, mock: bool = False):
        """
        Args:
            mock: Enable mock mode for testing without hardware
        """
        self.mock = mock
        self.connection = ConnectionClass(mock=mock)

    def initialize(self) -> None:
        """Initialize device and establish connection"""

    def perform_action(self, *args) -> Result:
        """Execute device-specific action"""
        if self.mock:
            return self._mock_action(*args)
        return self._real_action(*args)

    def get_status(self) -> Dict:
        """Query current device state"""

    def close(self) -> None:
        """Gracefully close connection"""
```

**Key Device Controllers**:

#### RobotController (`robot_controller.py`)

Controls SCARA robotic arm for physical manipulations:

```python
class RobotController:
    # Column operations
    def install_column(column_id: int) -> None
    def uninstall_column(column_id: int) -> None

    # Sample transfer
    def transfer_to_collect(bottle_id: int, position: int) -> None
    def collect_to_xuanzheng(bottle_id: int) -> None

    # Cleaning operations
    def to_clean_needle() -> None
    def get_penlin_needle() -> None

    # Home positions
    def robot_to_home() -> None
    def scara_to_home() -> None
```

#### XuanZHengController (`xuanzheng_device.py`)

Manages rotary evaporator via web interface automation:

```python
class XuanZHengController:
    def vacuum_until_below_threshold() -> None
    def run_evaporation() -> None
    def set_height(height_mm: int) -> None
    def drain_until_above_threshold() -> None
    def get_process() -> Dict[str, Any]
```

#### SepuService (`sepu_service.py`)

High-level chromatography operations:

```python
class SepuService:
    def wash_column(time_s: int) -> None
    def start_column(duration_min: int) -> None
    def select_retain_tubes(tubes: List[Dict]) -> None
    def save_experiment_data() -> None
    def update_line_start/pause/terminate() -> None
```

---

### Layer 4: Communication Layer (`src/com_control/`)

**Purpose**: Protocol implementations for device communication

```
src/com_control/
├── PLC_com.py              # Modbus TCP for PLCs
├── robot_com.py            # Socket communication
├── sepu_com.py             # HTTP REST client
├── xuanzheng_com.py        # Selenium WebDriver
├── opentrons_com.py        # Opentrons API client
└── redis/
    ├── producer.py         # Redis publish
    └── consumer.py         # Redis subscribe
```

**Communication Protocols**:

| Protocol | Use Case | Devices |
|----------|----------|---------|
| **Modbus TCP** | PLC control (registers, coils) | Pumps, height control |
| **Socket (TCP)** | Custom protocol, JSON/binary | SCARA robot |
| **HTTP REST** | High-level API calls | Chromatography system |
| **Selenium** | Web UI automation | Rotary evaporator |
| **Redis Pub/Sub** | Inter-service messaging | Distributed components |

---

## Communication Protocols

### 1. Modbus TCP (PLC Communication)

**File**: `src/com_control/PLC_com.py`

**Purpose**: Control pumps, valves, and sensors via industrial PLCs

**Implementation**:

```python
class PLCConnection:
    def __init__(self, ip: str, port: int):
        self.client = ModbusTcpClient(ip, port=port)

    def write_coil(self, address: int, value: bool) -> None:
        """Write single coil (ON/OFF control)"""

    def write_register(self, address: int, value: int) -> None:
        """Write holding register (numeric value)"""

    def read_coil(self, address: int) -> bool:
        """Read digital input"""

    def read_register(self, address: int) -> int:
        """Read analog input"""
```

**Example Usage**:

```python
# Start pump at register 300
plc.write_coil(300, True)

# Set pump time to 5 seconds (register 301)
plc.write_register(301, 50)  # Value in 0.1s units
```

**Device Mappings**:

| Device | Registers | Function |
|--------|-----------|----------|
| Peristaltic Pump | 300-302 | Start/stop, time, speed |
| Gear Pump | 200-202 | Start/stop, time |
| Height Control | 306-307 | Up/down movement |

---

### 2. Socket Communication (Robot Control)

**File**: `src/com_control/robot_com.py`

**Purpose**: Send commands to SCARA robot controller

**Protocol**: Custom JSON-based protocol over TCP sockets

**Implementation**:

```python
class RobotConnection:
    def __init__(self, ip: str, port: int):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((ip, port))

    def send_command(self, command: str, params: Dict) -> Dict:
        """Send JSON command and receive response"""
        message = json.dumps({
            'command': command,
            'params': params,
            'timestamp': time.time()
        })
        self.socket.sendall(message.encode())
        response = self.socket.recv(4096)
        return json.loads(response.decode())
```

**Example Commands**:

```json
// Install column
{
    "command": "install_column",
    "params": {"column_id": 6}
}

// Move to position
{
    "command": "move_to",
    "params": {"x": 100, "y": 200, "z": 50}
}
```

---

### 3. HTTP REST API (Chromatography System)

**File**: `src/com_control/sepu_com.py`

**Purpose**: Control chromatography system via HTTP API

**Endpoints**:

```python
BASE_URL = "http://192.168.1.20:8080/api/v1"

# Start experiment
POST /experiments/start
{
    "column_id": 6,
    "gradient": [...],
    "flow_rate": 20.0
}

# Get real-time data
GET /experiments/{id}/data
Response: {
    "time": 120.5,
    "absorbance": 0.543,
    "pressure": 150.2
}

# Control fraction collector
POST /fraction_collector/select
{
    "tubes": [1, 2, 3]
}
```

---

### 4. Selenium Web Automation (Rotary Evaporator)

**File**: `src/com_control/xuanzheng_com.py`

**Purpose**: Automate web-based rotary evaporator control panel

**Why Selenium?**: Legacy device only provides web UI, no API

**Implementation**:

```python
from selenium import webdriver
from selenium.webdriver.common.by import By

class XuanZHengConnection:
    def __init__(self, url: str):
        options = Options()
        options.add_argument('--headless')  # Run without GUI
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(url)

    def set_vacuum(self, pressure_mbar: int) -> None:
        """Set target vacuum pressure"""
        input_field = self.driver.find_element(By.ID, "vacuumInput")
        input_field.clear()
        input_field.send_keys(str(pressure_mbar))
        submit = self.driver.find_element(By.ID, "vacuumSubmit")
        submit.click()

    def get_status(self) -> Dict:
        """Scrape current status from web page"""
        status_div = self.driver.find_element(By.ID, "statusPanel")
        return parse_status_html(status_div.get_attribute('innerHTML'))
```

---

### 5. Redis Pub/Sub (Inter-Service Communication)

**Files**: `src/com_control/redis/producer.py`, `consumer.py`

**Purpose**: Real-time message passing between distributed components

**Use Cases**:
- GUI updates during workflow execution
- Alert notifications
- Distributed logging

**Example**:

```python
# Producer (in workflow)
from src.com_control.redis.producer import publish_message

publish_message('workflow_status', {
    'step': 'injection',
    'progress': 35,
    'timestamp': datetime.now().isoformat()
})

# Consumer (in GUI or monitoring service)
from src.com_control.redis.consumer import subscribe_to_channel

def handle_status_update(message):
    print(f"Step: {message['step']}, Progress: {message['progress']}%")

subscribe_to_channel('workflow_status', handle_status_update)
```

---

## Device Specifications

### Robot System

- **Type**: 6-axis SCARA (Selective Compliance Assembly Robot Arm)
- **Reach**: 600mm horizontal, 400mm vertical
- **Payload**: Up to 3kg
- **Repeatability**: ±0.05mm
- **Control**: Socket-based custom protocol
- **IP**: Configurable in `config/com_config.yaml`

**Coordinate System**:
```
Origin (0,0,0): Robot base center
+X: Right
+Y: Forward
+Z: Upward
```

---

### Chromatography System

- **Type**: High-Performance Liquid Chromatography (HPLC)
- **Detectors**: UV-Vis (190-800nm), optional MS
- **Flow Rate**: 0.1-50 mL/min
- **Pressure Limit**: 400 bar
- **Column Compatibility**: 1-12 positions
- **API**: HTTP REST (OpenAPI 3.0)
- **IP**: Configurable

**Data Output**:
- Real-time chromatogram (time vs. absorbance)
- Peak integration results
- Fraction collection logs

---

### Rotary Evaporator

- **Model**: Generic web-controlled rotavap
- **Vacuum Range**: 0-1000 mbar
- **Temperature**: 20-80°C water bath
- **Rotation Speed**: 20-280 rpm
- **Flask Size**: 50-5000 mL
- **Interface**: Web browser automation via Selenium
- **URL**: Configurable

---

### Pumps

#### Injection Pump
- **Type**: Syringe pump
- **Volume**: 1-25 mL
- **Accuracy**: ±1%
- **Control**: Modbus TCP
- **Registers**: 100-110

#### Peristaltic Pump
- **Flow Rate**: 0.1-200 mL/min
- **Tube Size**: 1/8" ID
- **Control**: Modbus TCP (registers 300-302)

#### Gear Pump
- **Type**: Positive displacement
- **Viscosity Range**: 1-1000 cP
- **Control**: Modbus TCP (registers 200-202)

---

## Data Flow

### Experiment Data Pipeline

```
┌──────────────┐
│  Raw Sensor  │  Chromatogram, pressure, temperature
│     Data     │
└──────┬───────┘
       │
┌──────▼───────┐
│   Device     │  Parse and validate sensor readings
│  Controllers│
└──────┬───────┘
       │
┌──────▼───────┐
│   Service    │  Calculate derived metrics (peaks, yields)
│    Layer     │
└──────┬───────┘
       │
       ├─────────────┐
       │             │
┌──────▼───────┐ ┌──▼────────┐
│   SQLite     │ │  Redis    │  Real-time + persistent storage
│   Database   │ │  Cache    │
└──────────────┘ └───────────┘
```

### Configuration Flow

```
config/com_config.yaml
       │
       ▼
src/util/yaml_control/setup.py (parse YAML)
       │
       ▼
device_control/__init__.py (initialize devices)
       │
       ▼
Device Controllers (use config values)
```

### Logging Flow

```
Device Operations
       │
       ▼
util/logs_control/setup.py (configure loggers)
       │
       ├────────────┬────────────┐
       │            │            │
┌──────▼──┐  ┌─────▼────┐  ┌───▼───┐
│ Console │  │   File   │  │ Redis │
│ Handler │  │ Handler  │  │Publish│
└─────────┘  └──────────┘  └───────┘
                  │
             logs/device_control.log
             logs/service_control.log
             logs/api.log
```

---

## Security & Safety

### Safety Mechanisms

1. **Emergency Stop**:
   ```python
   # Triggered by TaskController.stop()
   - Halt all pumps within 2 seconds
   - Release vacuum pressure
   - Return robot to safe home position
   - Log emergency stop event
   ```

2. **Interlocks**:
   - Vacuum cannot start unless flask is installed
   - Robot cannot move if pumps are running
   - Injection blocked during chromatography run

3. **Watchdog Timers**:
   - 300s timeout on all blocking operations
   - Automatic retry (3x) before failure escalation

4. **Error Recovery**:
   ```
   Device Communication Failure
           │
           ▼
   Retry with exponential backoff (1s, 2s, 4s)
           │
           ├─Success──► Continue workflow
           │
           ▼ Failure (3x)
   Log error + Trigger fallback
           │
           ├─Critical──► Emergency stop
           └─Non-critical──► Skip step + Continue
   ```

### Data Security

- **Configuration**: Sensitive IPs/ports in YAML (not committed to git)
- **Logging**: Sanitize sensitive parameters before logging
- **API**: Optional JWT authentication (configure in `app/main.py`)

---

## Deployment Architecture

### Single-Machine Deployment (Typical)

```
┌───────────────────────────────────────────────┐
│          Windows/Linux Host Machine           │
│                                               │
│  ┌─────────────────────────────────────────┐ │
│  │     FastAPI Server (port 8000)          │ │
│  └───────────┬─────────────────────────────┘ │
│              │                                │
│  ┌───────────▼─────────────────────────────┐ │
│  │     Workflow Orchestrator               │ │
│  └───┬───────┬───────┬───────┬─────────────┘ │
│      │       │       │       │                │
│  ┌───▼──┐┌───▼──┐┌───▼──┐┌───▼──┐           │
│  │Robot ││Sepu  ││Pumps ││Rotavap│           │
│  │Ctrl  ││Ctrl  ││Ctrl  ││Ctrl   │           │
│  └───┬──┘└───┬──┘└───┬──┘└───┬──┘           │
└──────┼───────┼───────┼───────┼───────────────┘
       │       │       │       │
       │(LAN Network - 192.168.1.x)
       │       │       │       │
┌──────▼──┐┌───▼──┐┌───▼──┐┌───▼──────┐
│ SCARA   ││ HPLC ││ PLCs ││ Rotavap  │
│ Robot   ││System││      ││(Browser) │
└─────────┘└──────┘└──────┘└──────────┘
```

### Network Configuration

```yaml
# config/com_config.yaml example
network:
  subnet: "192.168.1.0/24"
  gateway: "192.168.1.1"

devices:
  robot:
    ip: "192.168.1.10"
    port: 8080

  plc:
    ip: "192.168.1.100"
    port: 502

  chromatograph:
    ip: "192.168.1.20"
    port: 80

  rotary_evaporator:
    ip: "192.168.1.30"
    port: 5000
```

---

## Extension Points

### Adding a New Device

1. **Create communication layer** (`src/com_control/new_device_com.py`):
   ```python
   class NewDeviceConnection:
       def __init__(self, ip: str, port: int):
           # Implement protocol
       def send_command(self, cmd): ...
   ```

2. **Create device controller** (`src/device_control/new_device.py`):
   ```python
   class NewDeviceController:
       def __init__(self, mock=False):
           self.connection = NewDeviceConnection(...)
       def action(self): ...
   ```

3. **Register in device registry** (`src/device_control/__init__.py`):
   ```python
   from src.device_control.new_device import NewDeviceController
   new_device = NewDeviceController(mock=MOCK)
   ```

4. **Use in workflows** (`src/service_control/demo/modified_run_lab.py`):
   ```python
   from src.device_control import new_device
   await asyncio.to_thread(new_device.action)
   ```

---

## Performance Considerations

### Bottlenecks

1. **Selenium overhead**: Web automation adds 1-2s latency per call
   - **Mitigation**: Cache rotavap status, batch updates

2. **Sequential device operations**: Some steps must be strictly ordered
   - **Mitigation**: Parallelize independent operations (see Phase I in workflow)

3. **Network latency**: TCP round-trip time varies (5-50ms)
   - **Mitigation**: Use async I/O, avoid blocking main thread

### Optimization Strategies

- **Connection pooling**: Reuse TCP connections where possible
- **Caching**: Store device status to reduce polling frequency
- **Predictive start**: Begin slow operations early (e.g., pump initialization)

---

## Maintenance

### Log Locations

```
logs/
├── api.log               # FastAPI requests/responses
├── com.log               # Communication layer events
├── device_control.log    # Device actions and errors
├── service_control.log   # Workflow execution logs
└── yaml_control.log      # Configuration parsing
```

### Health Checks

Implement periodic health checks in `src/device_control/monitor.py`:

```python
def check_device_health():
    results = {}
    for device_name, device in get_all_devices():
        try:
            status = device.get_status()
            results[device_name] = "OK" if status else "DEGRADED"
        except Exception:
            results[device_name] = "DOWN"
    return results
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Robot not responding | Network disconnection | Check IP in config, ping robot |
| Modbus timeout | PLC offline or wrong address | Verify PLC IP, test with Modbus client |
| Selenium crash | ChromeDriver version mismatch | Update `chromedriver` to match Chrome |
| Import errors | Incorrect Python path | Ensure `PYTHONPATH` includes project root |
| Config not loading | YAML syntax error | Validate YAML with online parser |

### Debug Mode

Enable verbose logging:

```python
# In config/logging.yaml
loggers:
  root:
    level: DEBUG  # Change from INFO to DEBUG
```

---

**Document Version**: 2.0
**Last Updated**: 2024-11-06
**Maintainer**: Research Team
