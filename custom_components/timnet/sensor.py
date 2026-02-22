"""Sensor platform for TimNet Heating Controller integration."""
import logging
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.const import UnitOfTemperature, UnitOfTime
from homeassistant.helpers.entity import DeviceInfo

from .modbus_client import MinimalModbusTcpClient

_LOGGER = logging.getLogger(__name__)

DOMAIN = "timnet"
CONF_HOST = "host"
CONF_PORT = "port"
CONF_UNIT = "unit"
CONF_SCAN_INTERVAL = "scan_interval"

# TimNet register definitions according to manual
REGISTER_DEFINITIONS = [
    {
        "address": 0x0000,
        "name": "Temperature T1",
        "key": "TT",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "divider": 10,
        "icon": "mdi:thermometer"
    },
    {
        "address": 0x0001,
        "name": "Temperature T2",
        "key": "TT2",
        "unit": UnitOfTemperature.CELSIUS,
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "divider": 10,
        "icon": "mdi:thermometer",
        "timnet_200_only": True  # Hide on TimNet 100
    },
    {
        "address": 0x0002,
        "name": "Combustion Time",
        "key": "CAS",
        "unit": UnitOfTime.MINUTES,
        "device_class": SensorDeviceClass.DURATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "divider": 60,  # Convert seconds to minutes
        "icon": "mdi:fire-circle"
    },
    {
        "address": 0x0003,
        "name": "Flap Position",
        "key": "SER1",
        "unit": "%",
        "state_class": SensorStateClass.MEASUREMENT,
        "icon": "mdi:valve"
    },
    {
        "address": 0x0005,
        "name": "Combustion Mode",
        "key": "REZIM",
        "icon": "mdi:fire"
    },
    {
        "address": 0x0006,
        "name": "Fuel Type",
        "key": "PALIVO",
        "icon": "mdi:tree"
    },
    {
        "address": 0x0007,
        "name": "Refuel Offset",
        "key": "PRILOZ",
        "icon": "mdi:plus-minus"
    },
    {
        "address": 0x0008,
        "name": "SDS Sensitivity",
        "key": "SDS",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:tune"
    },
    {
        "address": 0x0009,
        "name": "Status Color",
        "key": "BARVA",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:palette"
    },
    {
        "address": 0x0010,
        "name": "Sound Signalization",
        "key": "BEEP",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:volume-high"
    },
    {
        "address": 0x0011,
        "name": "Relay 1",
        "key": "RELE1",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:electric-switch",
        "timnet_200_only": True  # Hide on TimNet 100
    },
    {
        "address": 0x0012,
        "name": "Relay 2",
        "key": "RELE2",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:electric-switch",
        "timnet_200_only": True  # Hide on TimNet 100
    },
    {
        "address": 0x0013,
        "name": "Sensor Fault",
        "key": "PORUCHA",
        "entity_category": EntityCategory.DIAGNOSTIC,
        "icon": "mdi:alert-circle"
    },
    {
        "address": 0x0014,
        "name": "Unit Status",
        "key": "STAT",
        "icon": "mdi:information"
    },
    {
        "address": 0x0015,
        "name": "Total Refuel Count",
        "key": "P_LIFE",
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "icon": "mdi:counter"
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up TimNet sensors."""
    config = entry.data
    host = config[CONF_HOST]
    port = config[CONF_PORT]
    unit = config.get(CONF_UNIT, 1)
    scan_interval = config.get(CONF_SCAN_INTERVAL, 8)

    coordinator = TimNetCoordinator(
        hass,
        host=host,
        port=port,
        unit=unit,
        scan_interval=scan_interval,
    )

    entities = []
    for reg_def in REGISTER_DEFINITIONS:
        # Skip TimNet 200-only sensors if T2 is inactive (indicates TimNet 100)
        if reg_def.get("timnet_200_only"):
            # Check if T2 register shows inactive value (20000, 20001, 20002)
            t2_value = coordinator.data.get(0x0001, 0)
            if t2_value in [20000, 20001, 20002]:
                _LOGGER.info(f"Skipping {reg_def['name']} (TimNet 200 only, device is TimNet 100)")
                continue
        
        entities.append(
            TimNetSensor(
                coordinator,
                entry,
                reg_def,
            )
        )
    
    # Add door switch binary sensor
    entities.append(
        TimNetDoorSensor(
            coordinator,
            entry,
        )
    )
    
    # Add connection status binary sensor
    entities.append(
        TimNetConnectionSensor(
            coordinator,
            entry,
        )
    )

    async_add_entities(entities)


class TimNetCoordinator(DataUpdateCoordinator):
    """Class to manage fetching TimNet data."""
        self.host = host
        self.port = port
        self.unit = unit
        self._last_valid_data: dict[int, int] = {}
        self.connection_ok: bool = True
        host: str,
        port: int,
        unit: int,
        scan_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.port = port
        self.unit = unit
        self._last_valid_data: dict[int, int] = {}

    async def _async_update_data(self) -> dict[int, int]:
        try:
            data = await self.hass.async_add_executor_job(self._fetch_data)
            if data:
                self._last_valid_data = data
                self.connection_ok = True
                return data
            else:
                self.connection_ok = False
                _LOGGER.warning(
                    "No data received from %s:%s - using last known values",
                    self.host,
                    self.port,
                )
                return self._last_valid_data
        except Exception as err:
            self.connection_ok = False
            _LOGGER.warning(
                "Error reading from %s:%s: %s - using last known values",
                self.host,
                self.port,
                err,
            )
            return self._last_valid_data
            return self._last_valid_data

    def _fetch_data(self) -> dict[int, int]:
        """Fetch data from TimNet device (runs in executor)."""
        client = MinimalModbusTcpClient(self.host, self.port, unit=self.unit)
        
        # Read registers 0-21 (covers all defined registers)
        values = client.read_holding_registers(0x0000, 22)
        
        data = {}
        for i, value in enumerate(values):
            data[i] = value
        
        return data


class TimNetSensor(CoordinatorEntity, SensorEntity):
    """Representation of a TimNet sensor."""

    # Status text mappings
    STATUS_MAP = {
        0: "Start napájení",
        1: "Klidový stav 100%",
        2: "Klidový stav 0%",
        3: "Zatápění",
        4: "Start regulace",
        5: "Hoření (vzrůstající teplota)",
        6: "Hoření (klesající teplota)",
        7: "Přiložit",
        8: "Žárový proces",
        10: "Nezatopeno",
        13: "Přetopeno",
        14: "Dlouho otevřená dvířka",
        15: "Testovací režim",
        20: "Porucha teploty",
    }

    MODE_MAP = {1: "Eco", 2: "Standard", 3: "Turbo"}
    FUEL_MAP = {1: "Dřevo", 2: "Brikety"}
    REFUEL_MAP = {1: "-2", 2: "-1", 3: "Standard", 4: "+1", 5: "+2"}
    COLOR_MAP = {0: "Bez barvy", 1: "Žlutá", 2: "Zelená", 3: "Červená"}
    BEEP_MAP = {0: "Vypnuto", 15: "Zapnuto"}
    RELAY_MAP = {0: "Rozepnuto", 1: "Sepnuto"}

    def __init__(
        self,
        coordinator: TimNetCoordinator,
        entry: ConfigEntry,
        reg_def: dict,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._reg_def = reg_def
        self._address = reg_def["address"]
        self._attr_name = f"TimNet {reg_def['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{reg_def['key']}"
        self._attr_has_entity_name = False
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TimNet Heating Controller",
            manufacturer="TimNet",
            model="TimNet 100/200",
        )
        
        # Set properties from definition
        if "unit" in reg_def:
            self._attr_native_unit_of_measurement = reg_def["unit"]
        if "device_class" in reg_def:
            self._attr_device_class = reg_def["device_class"]
        if "state_class" in reg_def:
            self._attr_state_class = reg_def["state_class"]
        if "entity_category" in reg_def:
            self._attr_entity_category = reg_def["entity_category"]
        if "icon" in reg_def:
            self._attr_icon = reg_def["icon"]

    @property
    def native_value(self) -> float | int | str | None:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
            
        raw_value = self.coordinator.data.get(self._address)
        if raw_value is None:
            return None

        key = self._reg_def["key"]
        
        # Handle temperature values (T1, T2)
        if key in ["TT", "TT2"]:
            if raw_value == 20000:
                return "HI"
            elif raw_value == -20000 or raw_value == 65536 - 20000:  # Handle negative as unsigned
                return "LO"
            elif raw_value == 20001:
                return "---"
            elif raw_value == 20002:
                return "Neaktivní"
            # Temperature is stored as value*10, divide to get °C
            if "divider" in self._reg_def:
                return round(raw_value / self._reg_def["divider"], 1)
            return raw_value
        
        # Handle combustion time (stored in seconds, display in minutes)
        if key == "CAS":
            if "divider" in self._reg_def:
                return round(raw_value / self._reg_def["divider"], 1)
            return raw_value
        
        # Handle flap position (0-100%, 255 = initializing)
        if key == "SER1":
            if raw_value == 255:
                return "Inicializace"
            # Direct percentage value
            return min(100, max(0, raw_value))
        
        # Handle SDS sensitivity
        if key == "SDS":
            if raw_value == 255:
                return "Vypnuto"
            active = raw_value % 10
            level = raw_value // 10
            level_map = {1: "-2", 2: "-1", 3: "Standard", 4: "+1", 5: "+2"}
            level_str = level_map.get(level, "Neznámé")
            return f"{level_str} {'(Aktivní)' if active == 1 else '(Neaktivní)'}"
        
        # Handle text mappings
        if key == "STAT":
            return self.STATUS_MAP.get(raw_value, f"Neznámý ({raw_value})")
        if key == "REZIM":
            return self.MODE_MAP.get(raw_value, raw_value)
        if key == "PALIVO":
            return self.FUEL_MAP.get(raw_value, raw_value)
        if key == "PRILOZ":
            return self.REFUEL_MAP.get(raw_value, raw_value)
        if key == "BARVA":
            return self.COLOR_MAP.get(raw_value, raw_value)
        if key == "BEEP":
            return self.BEEP_MAP.get(raw_value, raw_value)
        if key in ["RELE1", "RELE2"]:
            return self.RELAY_MAP.get(raw_value, raw_value)
        
        # Handle sensor fault (additive values)
        if key == "PORUCHA":
            if raw_value == 0:
                return "Bez poruchy"
            faults = []
            if raw_value & 1:
                faults.append("T1")
            if raw_value & 2:
                faults.append("T2")
            if raw_value & 8:
                faults.append("Dvířka")
            return ", ".join(faults) if faults else f"Neznámá ({raw_value})"
        
        # Default: return raw value (possibly with divider)
        if "divider" in self._reg_def:
            return round(raw_value / self._reg_def["divider"], 1)
        
        return raw_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            "address": f"0x{self._address:04X}",
            "register_key": self._reg_def["key"],
            "host": self.coordinator.host,
            "port": self.coordinator.port,
        }
        
        # Add raw value for debugging
        if self.coordinator.data:
            raw_value = self.coordinator.data.get(self._address)
            if raw_value is not None:
                attrs["raw_value"] = raw_value
        
        return attrs


class TimNetDoorSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of TimNet door switch sensor."""

    def __init__(
        self,
        coordinator: TimNetCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the door sensor."""
        super().__init__(coordinator)
        self._attr_name = "TimNet Door Switch"
        self._attr_unique_id = f"{entry.entry_id}_door"
        self._attr_has_entity_name = False
        self._attr_device_class = BinarySensorDeviceClass.DOOR
        self._attr_icon = "mdi:door"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TimNet Heating Controller",
            manufacturer="TimNet",
            model="TimNet 100/200",
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if door is open."""
        if not self.coordinator.data:
            return None
            
        # Door switch is at register 0x0004
        # 0 = closed, 255 = open
        raw_value = self.coordinator.data.get(0x0004)
        if raw_value is None:
            return None
        
        return raw_value != 0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        attrs = {
            "address": "0x0004",
            "register_key": "INP",
            "host": self.coordinator.host,
            "port": self.coordinator.port,
        }
        
        if self.coordinator.data:
            raw_value = self.coordinator.data.get(0x0004)
            if raw_value is not None:
                attrs["raw_value"] = raw_value
        
        return attrs


class TimNetConnectionSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of TimNet connection status sensor."""

    def __init__(
        self,
        coordinator: TimNetCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the connection sensor."""
        super().__init__(coordinator)
        self._attr_name = "TimNet Connection Status"
        self._attr_unique_id = f"{entry.entry_id}_connection"
        self._attr_has_entity_name = False
        self._attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:lan-connect"
        
        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TimNet Heating Controller",
            manufacturer="TimNet",
            model="TimNet 100/200",
        )

    @property
    def is_on(self) -> bool:
        """Return true if connected."""
        return self.coordinator.connection_ok and bool(self.coordinator.data)

    @property
    def available(self) -> bool:
        """Connection sensor is always available."""
        return True

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        return {
            "host": self.coordinator.host,
            "port": self.coordinator.port,
        }
