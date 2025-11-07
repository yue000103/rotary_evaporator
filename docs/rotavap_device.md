# Rotavap Device Control Reference

## 1. Module Overview

- **Entry point**: `RotavapController` wraps the HTTP automation API (`ConnectionController`) and PLC I/O (`src.com_control.plc`) to orchestrate heating, cooling, vacuum, rotation, lift, waste handling, and bottle height automation.
- **Mock mode**: `RotavapController(mock=True)` routes all calls through simulated transports; safety routines short-circuit with informative logs rather than touching hardware.
- **Context management**: Implements `__enter__` / `__exit__`; calling `close()` always tears down the underlying connection and logs teardown failures.

## 2. PLC Register & Coil Map

| Symbol | Address | Purpose |
| --- | --- | --- |
| `HEIGHT_ADDRESS` | 502 | Target lift height register written before auto moves. |
| `AUTO_SET` | 500 | Coil pulse that triggers automatic height positioning. |
| `AUTO_FINISH` | 501 | Completion coil polled by `_wait_height_finish()`; True indicates height move completed. |
| `WASTE_LIQUID` | 323 | Coil pulse that starts the waste-drain cycle. |
| `WASTE_LIQUID_FINISH` | 333 | Completion coil polled by `_wait_waste_finish()`; True indicates waste draining finished. |

## 3. Command Set

### 3.1 HTTP API Commands

| Method | Endpoint | Payload / Result |
| --- | --- | --- |
| `get_info()` | `GET /api/v1/info` | Static controller metadata parsed by `_parse_response()`. |
| `get_process()` | `GET /api/v1/process` | Live telemetry used to populate `DeviceStatus`. |
| `change_device_parameters()` | `PUT /api/v1/process` | Accepts any combination of configs below plus optional `globalStatus` or `program` blocks; logs all mutated keys. |

**Payload dataclasses**

| Dataclass | Fields | Notes |
| --- | --- | --- |
| `HeatingConfig` | `set`, `running` | Heater target temperature (°C) and run flag. |
| `CoolingConfig` | `set`, `running` | Chiller target temperature (°C) and run flag. |
| `VacuumConfig` | `set`, `vacuumValveOpen`, `aerateValveOpen`, `aerateValvePulse` | Defaults to `DEFAULT_VACUUM_SET = 150 mbar`. |
| `RotationConfig` | `set`, `running` | Rotation speed and enable flag. |
| `LiftConfig` | `set` | Lift position units defined by vendor API. |
| `ProgramConfig` | `type`, `endVacuum`, `flaskSize` | Program type defaults to `AutoDest`; `flaskSize` derives from `FlaskSize`. |

### 3.2 PLC / IO Helpers

| Routine | Description |
| --- | --- |
| `set_height(volume)` | Maps flask volume to lift target and `flaskSize`, writes `HEIGHT_ADDRESS`, optionally sends `ProgramConfig`, pulses `AUTO_SET`, and waits for `_wait_height_finish()`. |
| `_wait_height_finish(timeout=120 s)` | Polls `AUTO_FINISH` every 2 s; raises `TimeoutError` if exceeded. |
| `start_waste_liquid(wait_for_completion=False, timeout=60 s)` | Pulses `WASTE_LIQUID`; optionally waits via `_wait_waste_finish()`. |
| `_wait_waste_finish(timeout=60 s)` | Polls `WASTE_LIQUID_FINISH` every 1 s until done or timeout. |

### 3.3 Process Control Routines

| Routine | Description |
| --- | --- |
| `run_evaporation(delay=10 s)` | Sets `globalStatus.running=True` and waits the given delay before returning the response. |
| `stop_evaporation()` | Sends `globalStatus.running=False`. |
| `xuanzheng_sync(timeout_min=120, poll_interval=2 s)` | Monitors `DeviceStatus.running` to detect start and finish; stops evaporation automatically on timeout. |

### 3.4 Vacuum / Pressure Controls

| Routine | Description |
| --- | --- |
| `run_vacuum()` | Issues `VacuumConfig(set=DEFAULT_VACUUM_SET, vacuumValveOpen=True)` plus `LiftConfig(set=DEFAULT_LIFT_SET)` in one request. |
| `stop_vacuum()` | Sends the same payload with `vacuumValveOpen=False`. |
| `drain_valve_open(duration=5 s)` | Opens the aeration valve (no pulse) for the specified duration. |
| `vacuum_until_below_threshold(threshold=400 mbar, poll_interval=1 s)` | Loops on `get_device_status()` until `vacuum_actual` is below the threshold; always calls `stop_vacuum()` on success or exception. |
| `drain_until_above_threshold(threshold=900 mbar, poll_interval=1 s, wait_after=5 s)` | Kicks off `drain_valve_open(duration=0)` once, polls until `vacuum_actual` rises above the threshold, then waits `wait_after` seconds for stabilization. |

## 4. Device Status Model

`get_device_status()` wraps `get_process()` output into `DeviceStatus` with:

- `running`: mirrors `globalStatus.running`.
- `vacuum_actual`: instantaneous vacuum (mbar).
- `heating_actual`, `cooling_actual`: actual temperatures reported by subsystems.
- `rotation_actual`: measured RPM.

These signals drive all safety loops (vacuum threshold waits, `xuanzheng_sync`, etc.).

## 5. Timeouts & Polling

| Context | Value | Notes |
| --- | --- | --- |
| `DEFAULT_POLL_INTERVAL` | 2 s | Used by `xuanzheng_sync` unless overridden. |
| `DEFAULT_SYNC_TIMEOUT` | 120 min | Converted to seconds internally for the sync loop. |
| `_wait_height_finish` timeout | 120 s | Raises `TimeoutError` when exceeded. |
| `_wait_waste_finish` timeout | 60 s | Raises `TimeoutError` when exceeded. |
| Vacuum threshold loops | 1 s (default) | Configurable per call. |
| Waste pulse delays | 1 s coil high, 2 s settle | Hard-coded inside `start_waste_liquid`. |
| Auto-set delays | 1 s after writing height, 3 s after setting `AUTO_SET`, 1 s before resetting coil | Embedded in `set_height()`. |

## 6. Calibration / Height Table

`VOLUME_HEIGHT_MAP` enforces calibrated lift positions for common flask volumes:

| Volume (mL) | Lift setpoint (`VolumeHeight`) | Flask size |
| --- | --- | --- |
| 1000 | 1050 (`VOLUME_1000ML`) | `FlaskSize.LARGE` |
| 500 | 1150 (`VOLUME_500ML`) | `FlaskSize.SMALL` |
| 100 | 1400 (`VOLUME_100ML`) | `FlaskSize.SMALL` |
| 50 | 1417 (`VOLUME_50ML`) | `FlaskSize.SMALL` |
| 0 | 0 (`VOLUME_0ML`) | `FlaskSize.SMALL` (home position) |

Unsupported volumes raise `ValueError` with the allowed list.

## 7. Fault Protection & Recovery

- **Timeout enforcement**: Height, waste, and sync routines all raise or return failures when deadlines are exceeded, preventing indefinite blocking.
- **Vacuum safety**: Threshold loops guarantee `stop_vacuum()` runs even when exceptions occur, ensuring pumps do not run unattended.
- **Waste handling fallback**: `start_waste_liquid()` returns `False` if PLC writes fail so upstream workflow logic can retry or abort.
- **Connection cleanup**: `close()` is called automatically when using the controller as a context manager; teardown errors are logged as warnings.
- **Verbose diagnostics**: Every API/PLC failure path emits `logger.error`/`logger.warning` messages with exception context.
- **Mock isolation**: When `mock=True`, routines skip hardware operations but preserve state transitions in the logs, enabling safe dry runs.

