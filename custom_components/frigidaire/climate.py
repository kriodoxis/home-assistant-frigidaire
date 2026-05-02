"""ClimateEntity for frigidaire integration."""
from __future__ import annotations

import logging
from typing import Optional, List, Mapping, Any, Dict

import frigidaire

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    FAN_OFF,
    PRESET_NONE,
    PRESET_SLEEP,
    SWING_OFF,
    SWING_VERTICAL,
    HVACMode,
    ClimateEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _normalize_enum_value(value):
    """Normalize API values to uppercase for enum comparison."""
    if isinstance(value, str):
        return value.upper()
    return value


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up frigidaire from a config entry."""
    client = hass.data[DOMAIN][entry.entry_id]

    def get_entities(username: str, password: str) -> List[frigidaire.Appliance]:
        return client.get_appliances()

    appliances = await hass.async_add_executor_job(
        get_entities, entry.data["username"], entry.data["password"]
    )

    async_add_entities(
        [
            FrigidaireClimate(client, appliance)
            for appliance in appliances
            if appliance.destination == frigidaire.Destination.AIR_CONDITIONER
        ],
        update_before_add=True,
    )


FRIGIDAIRE_TO_HA_UNIT = {
    frigidaire.Unit.FAHRENHEIT: UnitOfTemperature.FAHRENHEIT,
    frigidaire.Unit.CELSIUS: UnitOfTemperature.CELSIUS,
}

FRIGIDAIRE_TO_HA_MODE = {
    frigidaire.Mode.OFF: HVACMode.OFF,
    frigidaire.Mode.COOL: HVACMode.COOL,
    frigidaire.Mode.FAN: HVACMode.FAN_ONLY,
    frigidaire.Mode.ECO: HVACMode.AUTO,
    frigidaire.Mode.AUTO: HVACMode.AUTO,
    frigidaire.Mode.DRY: HVACMode.DRY,
}

FRIGIDAIRE_TO_HA_PRESET = {
    frigidaire.SleepMode.OFF: PRESET_NONE,
    frigidaire.SleepMode.ON: PRESET_SLEEP
}

FRIGIDAIRE_TO_HA_SWING = {
    frigidaire.VerticalSwing.OFF: SWING_OFF,
    frigidaire.VerticalSwing.ON: SWING_VERTICAL
}

FRIGIDAIRE_TO_HA_FAN_SPEED = {
    frigidaire.FanSpeed.AUTO: FAN_AUTO,
    frigidaire.FanSpeed.LOW: FAN_LOW,
    frigidaire.FanSpeed.MEDIUM: FAN_MEDIUM,
    frigidaire.FanSpeed.HIGH: FAN_HIGH,
}

HA_TO_FRIGIDAIRE_UNIT = {
    UnitOfTemperature.FAHRENHEIT: frigidaire.Unit.FAHRENHEIT,
    UnitOfTemperature.CELSIUS: frigidaire.Unit.CELSIUS,
}

HA_TO_FRIGIDAIRE_FAN_MODE = {
    FAN_AUTO: frigidaire.FanSpeed.AUTO,
    FAN_LOW: frigidaire.FanSpeed.LOW,
    FAN_MEDIUM: frigidaire.FanSpeed.MEDIUM,
    FAN_HIGH: frigidaire.FanSpeed.HIGH,
}

HA_TO_FRIGIDAIRE_PRESET = {
    PRESET_NONE: frigidaire.SleepMode.OFF,
    PRESET_SLEEP: frigidaire.SleepMode.ON
}

HA_TO_FRIGIDAIRE_SWING = {
    SWING_OFF: frigidaire.VerticalSwing.OFF,
    SWING_VERTICAL: frigidaire.VerticalSwing.ON
}

HA_TO_FRIGIDAIRE_HVAC_MODE = {
    HVACMode.AUTO: frigidaire.Mode.ECO,
    HVACMode.FAN_ONLY: frigidaire.Mode.FAN,
    HVACMode.COOL: frigidaire.Mode.COOL,
    HVACMode.OFF: frigidaire.Mode.OFF,
    HVACMode.DRY: frigidaire.Mode.DRY,
}


class FrigidaireClimate(ClimateEntity):
    """Representation of a Frigidaire appliance."""

    def __init__(self, client, appliance):
        """Build FrigidaireClimate.

        client: the client used to contact the frigidaire API
        appliance: the basic information about the frigidaire appliance, used to contact
            the API
        """

        self._client: frigidaire.Frigidaire = client
        self._appliance: frigidaire.Appliance = appliance
        self._details: Optional[Dict] = None

        # Entity Class Attributes
        self._attr_unique_id = self._appliance.appliance_id
        self._attr_name = self._appliance.nickname
        self._attr_supported_features = (ClimateEntityFeature.TARGET_TEMPERATURE |
                                         ClimateEntityFeature.FAN_MODE |
                                         ClimateEntityFeature.TURN_OFF |
                                         ClimateEntityFeature.TURN_ON |
                                         ClimateEntityFeature.SWING_MODE |
                                         ClimateEntityFeature.PRESET_MODE)
        self._attr_target_temperature_step = 1

        # Although we can access the Frigidaire API to get updates, they are
        # not reflected immediately after making a request. To improve the UX
        # around this, we set assume_state to True
        self._attr_assumed_state = True

        self._attr_preset_modes = [
            PRESET_NONE,
            PRESET_SLEEP
        ]

        self._attr_swing_modes = [
            SWING_OFF,
            SWING_VERTICAL
        ]

        self._attr_fan_modes = [
            FAN_AUTO,
            FAN_LOW,
            FAN_MEDIUM,
            FAN_HIGH,
        ]

        self._attr_hvac_modes = [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.AUTO,
            HVACMode.FAN_ONLY,
            HVACMode.DRY,
        ]

    @property
    def assumed_state(self):
        """Return True if unable to access real state of the entity."""
        return self._attr_assumed_state

    @property
    def unique_id(self):
        """Return unique ID based on Frigidaire ID."""
        return self._attr_unique_id

    @property
    def name(self):
        """Return the name of the entity."""
        return self._attr_name

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return self._attr_supported_features

    @property
    def hvac_modes(self):
        """List of available operation modes."""
        return self._attr_hvac_modes

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._attr_target_temperature_step

    @property
    def fan_modes(self):
        """List of available fan modes."""
        return self._attr_fan_modes

    @property
    def temperature_unit(self):
        """Return the unit of measurement which this thermostat uses."""
        unit = _normalize_enum_value(self._details.get(
            frigidaire.Detail.TEMPERATURE_REPRESENTATION
        ))

        return FRIGIDAIRE_TO_HA_UNIT[unit]
    
    @property
    def swing_mode(self):
        """Return the swing setting."""
        swing = _normalize_enum_value(self._details.get(
            frigidaire.Detail.VERTICAL_SWING
        ))

        return FRIGIDAIRE_TO_HA_SWING[swing]

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return self._details.get(frigidaire.Detail.TARGET_TEMPERATURE_F)
        else:
            return self._details.get(frigidaire.Detail.TARGET_TEMPERATURE_C)
        
    @property
    def preset_mode(self):
        """Return current preset mode."""
        sleep = _normalize_enum_value(
            self._details.get(frigidaire.Detail.SLEEP_MODE)
        )
        sleep_norm = _normalize_enum_value(sleep)
        _LOGGER.debug("PRESET MODE: raw=%s, normalized=%s, mapped=%s", sleep, sleep_norm, FRIGIDAIRE_TO_HA_PRESET.get(sleep_norm))
        return FRIGIDAIRE_TO_HA_PRESET[sleep_norm]

    @property
    def hvac_mode(self):
        """Return current operation i.e. heat, cool, idle."""
        appliance_state = _normalize_enum_value(
            self._details.get(frigidaire.Detail.APPLIANCE_STATE)
        )
        
        if appliance_state in ["OFF", "DELAYED_START"]:
            return HVACMode.OFF
    
        frigidaire_mode = _normalize_enum_value(
            self._details.get(frigidaire.Detail.MODE)
        )
    
        return FRIGIDAIRE_TO_HA_MODE[frigidaire_mode]

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return self._details.get(frigidaire.Detail.AMBIENT_TEMPERATURE_F)
        else:
            return self._details.get(frigidaire.Detail.AMBIENT_TEMPERATURE_C)

    @property
    def fan_mode(self):
        """Return the fan setting."""
        fan_speed = _normalize_enum_value(self._details.get(frigidaire.Detail.FAN_SPEED))

        if not fan_speed:
            return FAN_OFF

        return FRIGIDAIRE_TO_HA_FAN_SPEED[fan_speed]

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return 60

        return 16

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        if self.temperature_unit == UnitOfTemperature.FAHRENHEIT:
            return 90

        return 32

    @property
    def extra_state_attributes(self) -> Mapping[str, Any] | None:
        return {
            "check_filter": bool(
                _normalize_enum_value(self._details.get(frigidaire.Detail.FILTER_STATE)) == "CHANGE"
            ),
        }

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        temperature = kwargs.get(ATTR_TEMPERATURE)
        if temperature is None:
            return
        temperature = int(temperature)
        temperature_unit = HA_TO_FRIGIDAIRE_UNIT[self.temperature_unit]

        _LOGGER.debug("Setting temperature to int({}) {}".format(temperature, self.temperature_unit))
        self._client.execute_action(
            self._appliance, frigidaire.Action.set_temperature(temperature, temperature_unit)
        )

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        # Guard against unexpected fan modes
        if fan_mode not in HA_TO_FRIGIDAIRE_FAN_MODE:
            return

        action = frigidaire.Action.set_fan_speed(HA_TO_FRIGIDAIRE_FAN_MODE[fan_mode])
        self._client.execute_action(self._appliance, action)

    def set_preset_mode(self, preset_mode) -> None:
        """Set new preset mode."""
        if preset_mode == PRESET_SLEEP:
            action = frigidaire.Action.set_sleep_mode(frigidaire.SleepMode.ON)
        elif preset_mode == PRESET_NONE:
            action = frigidaire.Action.set_sleep_mode(frigidaire.SleepMode.OFF)
        else:
            return

        self._client.execute_action(self._appliance, action)

    def set_swing_mode(self, preset_mode) -> None:
        """Set new swing mode."""
        if preset_mode == SWING_VERTICAL:
            action = frigidaire.Action.set_vertical_swing(frigidaire.VerticalSwing.ON)
        elif preset_mode == SWING_OFF:
            action = frigidaire.Action.set_vertical_swing(frigidaire.VerticalSwing.OFF)
        else:
            return

        self._client.execute_action(self._appliance, action)

    def set_hvac_mode(self, hvac_mode):
        """Set new target operation mode."""
        _LOGGER.debug("Setting HVAC mode to %s", hvac_mode)
        if hvac_mode == HVACMode.OFF:
            self._client.execute_action(
                self._appliance,
                frigidaire.Action.set_mode(frigidaire.Mode.OFF),
            )
            return

        # Guard against unexpected hvac modes
        if hvac_mode not in HA_TO_FRIGIDAIRE_HVAC_MODE:
            return

        # Turn on if not currently on.
        if _normalize_enum_value(self._details.get(frigidaire.Detail.MODE)) == frigidaire.Mode.OFF:
            self._client.execute_action(
                self._appliance, frigidaire.Action.set_power(frigidaire.Power.ON)
            )

            # temperature reverts to default when the device is turned on
            self._client.execute_action(
                self._appliance,
                frigidaire.Action.set_temperature(int(self.target_temperature))
            )

        self._client.execute_action(
            self._appliance,
            frigidaire.Action.set_mode(HA_TO_FRIGIDAIRE_HVAC_MODE[hvac_mode]),
        )

    def update(self):
        """Retrieve latest state and updates the details."""
        try:
            details = self._client.get_appliance_details(self._appliance)
            _LOGGER.debug("Retrieved details for appliance %s: %s", self._appliance.appliance_id, details)
            self._details = details
        except frigidaire.FrigidaireException:
            if self.available:
                _LOGGER.error("Failed to connect to Frigidaire servers")
            self._attr_available = False
        else:
            # If we successfully retrieved details, the appliance is available
            # Check that we have a valid applianceState
            appliance_state = self._details.get(frigidaire.Detail.APPLIANCE_STATE)
            self._attr_available = appliance_state is not None
            
            # Log detailed mapping information
            try:
                appliance_state = self._details.get(frigidaire.Detail.APPLIANCE_STATE)
                _LOGGER.debug("APPLIANCE_STATE: raw=%s", appliance_state)

                temp_repr = self._details.get(frigidaire.Detail.TEMPERATURE_REPRESENTATION)
                temp_repr_norm = _normalize_enum_value(temp_repr)
                _LOGGER.debug("TEMPERATURE_REPRESENTATION: raw=%s, normalized=%s, mapped=%s", 
                              temp_repr,
                              temp_repr_norm,
                              FRIGIDAIRE_TO_HA_UNIT.get(temp_repr_norm))
                
                mode = self._details.get(frigidaire.Detail.MODE)
                mode_norm = _normalize_enum_value(mode)
                _LOGGER.debug("MODE: raw=%s, normalized=%s, mapped=%s",
                              mode,
                              mode_norm,
                              FRIGIDAIRE_TO_HA_MODE.get(mode_norm))
                
                fan_speed = self._details.get(frigidaire.Detail.FAN_SPEED)
                fan_speed_norm = _normalize_enum_value(fan_speed)
                _LOGGER.debug("FAN_SPEED: raw=%s, normalized=%s, mapped=%s",
                              fan_speed,
                              fan_speed_norm,
                              FRIGIDAIRE_TO_HA_FAN_SPEED.get(fan_speed_norm))
                
                target_temp_f = self._details.get(frigidaire.Detail.TARGET_TEMPERATURE_F)
                target_temp_c = self._details.get(frigidaire.Detail.TARGET_TEMPERATURE_C)
                _LOGGER.debug("TARGET_TEMPERATURE: F=%s, C=%s", target_temp_f, target_temp_c)
                
                ambient_temp_f = self._details.get(frigidaire.Detail.AMBIENT_TEMPERATURE_F)
                ambient_temp_c = self._details.get(frigidaire.Detail.AMBIENT_TEMPERATURE_C)
                _LOGGER.debug("AMBIENT_TEMPERATURE: F=%s, C=%s", ambient_temp_f, ambient_temp_c)
                
                filter_state = self._details.get(frigidaire.Detail.FILTER_STATE)
                filter_state_norm = _normalize_enum_value(filter_state)
                _LOGGER.debug("FILTER_STATE: raw=%s, normalized=%s, is_change=%s",
                              filter_state, filter_state_norm, filter_state_norm == "CHANGE")
                
                sleep_mode = self._details.get(frigidaire.Detail.SLEEP_MODE)
                sleep_mode_norm = _normalize_enum_value(sleep_mode)
                _LOGGER.debug("SLEEP_MODE: raw=%s, normalized=%s, mapped=%s",
                              sleep_mode, sleep_mode_norm, FRIGIDAIRE_TO_HA_PRESET.get(sleep_mode_norm))
                
                vertical_swing = self._details.get(frigidaire.Detail.VERTICAL_SWING)
                vertical_swing_norm = _normalize_enum_value(vertical_swing)
                _LOGGER.debug("VERTICAL_SWING: raw=%s, normalized=%s, mapped=%s",
                              vertical_swing, vertical_swing_norm, FRIGIDAIRE_TO_HA_SWING.get(vertical_swing_norm))
            except Exception as e:
                _LOGGER.error("Error logging detail mappings: %s", e)
