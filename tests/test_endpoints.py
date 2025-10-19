"""Test endpoint for envoy v7 and newer firmware"""

import contextlib
import json
import logging
from typing import Any

import aiohttp
import orjson
import pytest
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.const import (
    PhaseNames,
)
from pyenphase.envoy import EnvoyProbeFailed, SupportedFeatures
from pyenphase.models.meters import CtMeterStatus, CtType, EnvoyPhaseMode

from .common import (
    endpoint_path,
    get_mock_envoy,
    latest_request,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
    temporary_log_level,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    (
        "version",
        "part_number",
        "supported_features",
        "updaters",
        "phase_count",
        "common_properties",
        "production_phases",
        "consumption_phases",
        "ct_production",
        "ct_consumption",
        "ct_storage",
        "ct_production_phases",
        "ct_consumption_phases",
        "ct_storage_phases",
    ),
    [
        (
            "5.0.62",
            "800-00551-r02",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "4.10.35",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 166,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 567,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 83,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 84,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": 394,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 173,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
        ),
        (
            "7.3.130",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.130_no_consumption",
            "800-00647-r10",
            SupportedFeatures.METERING
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 1,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": None,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 3625,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 1811,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 1814,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
            {},
        ),
        (
            "7.3.517",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.517_legacy_savings_mode",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.3.517_system_2",
            "800-00555-r03",
            SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 2660,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 23,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 1331,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 1329,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -17,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 41,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
        ),
        (
            "7.3.466_metered_disabled_cts",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.114_without_cts",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175",
            "800-00555-r03",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_total",
            "800-00654-r06",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_standard",
            "800-00656-r06",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_with_cts",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
            },
            1,
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "7.6.175_with_cts_3phase",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.THREEPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.THREEPHASE
                | SupportedFeatures.CTMETERS,
            },
            3,
            {
                "ctMeters": 2,
                "phaseCount": 3,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 1869678,
                    "watt_hours_last_7_days": 29891,
                    "watt_hours_today": 2200,
                    "watts_now": -3,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 1241246,
                    "watt_hours_last_7_days": 19794,
                    "watt_hours_today": 1455,
                    "watts_now": 0,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 1240189,
                    "watt_hours_last_7_days": 19807,
                    "watt_hours_today": 1458,
                    "watts_now": -4,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 2293783,
                    "watt_hours_last_7_days": 39392,
                    "watt_hours_today": 8585,
                    "watts_now": 89,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 948058,
                    "watt_hours_last_7_days": 18949,
                    "watt_hours_today": 2155,
                    "watts_now": 123,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 832954,
                    "watt_hours_last_7_days": 10443,
                    "watt_hours_today": 1683,
                    "watts_now": -3,
                },
            },
            {
                "eid": 704643328,
                "active_power": 489,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": -36,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 489,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 0,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385171,
                    "active_power": -1,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -36,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385427,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
        ),
        (
            "7.3.466_with_cts_3phase",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.THREEPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.THREEPHASE
                | SupportedFeatures.CTMETERS,
            },
            3,
            {
                "ctMeters": 2,
                "phaseCount": 3,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 1869678,
                    "watt_hours_last_7_days": 29891,
                    "watt_hours_today": 2200,
                    "watts_now": -3,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 1241246,
                    "watt_hours_last_7_days": 19794,
                    "watt_hours_today": 1455,
                    "watts_now": 0,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 1240189,
                    "watt_hours_last_7_days": 19807,
                    "watt_hours_today": 1458,
                    "watts_now": -4,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 2293783,
                    "watt_hours_last_7_days": 39392,
                    "watt_hours_today": 8585,
                    "watts_now": 89,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 948058,
                    "watt_hours_last_7_days": 18949,
                    "watt_hours_today": 2155,
                    "watts_now": 123,
                },
                PhaseNames.PHASE_3: {
                    "watt_hours_lifetime": 832954,
                    "watt_hours_last_7_days": 10443,
                    "watt_hours_today": 1683,
                    "watts_now": -3,
                },
            },
            {
                "eid": 704643328,
                "active_power": 489,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": -36,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 489,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 0,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385171,
                    "active_power": -1,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -36,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_3: {
                    "eid": 1778385427,
                    "active_power": -0,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
        ),
        (
            "7.6.185_with_cts_and_battery_3t",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
            },
            1,
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "8.1.41",
            "800-00664-r05",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENPOWER
                | SupportedFeatures.ENCHARGE,
                "EnvoyProductionJsonUpdater": SupportedFeatures.PRODUCTION
                | SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "8.2.127_with_3cts_and_battery_split",
            "800-00654-r08",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.ENPOWER,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 3,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": CtType.STORAGE,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 1714,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 129,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643840,
                "active_power": -2580,
                "measurement_type": CtType.STORAGE,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 856,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 858,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": -201,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 331,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385681,
                    "active_power": -2115,
                    "measurement_type": CtType.STORAGE,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385682,
                    "active_power": -465,
                    "measurement_type": CtType.STORAGE,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
        ),
        (
            "8.2.127_with_generator_running",
            "800-00647-r09",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS
            | SupportedFeatures.GENERATOR,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.ENPOWER,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
                "EnvoyGeneratorUpdater": SupportedFeatures.GENERATOR,
            },
            2,
            {
                "ctMeters": 2,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {
                "eid": 704643328,
                "active_power": 2336,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 196,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {},
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 1173,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 1163,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": 268,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": -72,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {},
        ),
        (
            "8.2.4286_with_3cts_and_battery_split",
            "800-00664-r05",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.TARIFF
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.CTMETERS,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.ENPOWER,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
                "EnvoyMetersUpdater": SupportedFeatures.DUALPHASE
                | SupportedFeatures.CTMETERS,
            },
            2,
            {
                "ctMeters": 3,
                "phaseCount": 2,
                "phaseMode": EnvoyPhaseMode.SPLIT,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": CtType.STORAGE,
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 6709433,
                    "watt_hours_last_7_days": 6703259,
                    "watt_hours_today": 6277,
                    "watts_now": 3559,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 6721896,
                    "watt_hours_last_7_days": 6715706,
                    "watt_hours_today": 6293,
                    "watts_now": 3564,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "watt_hours_lifetime": 7197821,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 4407,
                },
                PhaseNames.PHASE_2: {
                    "watt_hours_lifetime": 7915653,
                    "watt_hours_last_7_days": 0,
                    "watt_hours_today": 0,
                    "watts_now": 4478,
                },
            },
            {
                "eid": 704643328,
                "active_power": 7131,
                "measurement_type": CtType.PRODUCTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643584,
                "active_power": 1750,
                "measurement_type": CtType.NET_CONSUMPTION,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                "eid": 704643840,
                "active_power": -7084,
                "measurement_type": CtType.STORAGE,
                "metering_status": CtMeterStatus.NORMAL,
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385169,
                    "active_power": 3562,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385170,
                    "active_power": 3569,
                    "measurement_type": CtType.PRODUCTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385425,
                    "active_power": 810,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385426,
                    "active_power": 940,
                    "measurement_type": CtType.NET_CONSUMPTION,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
            {
                PhaseNames.PHASE_1: {
                    "eid": 1778385681,
                    "active_power": -3538,
                    "measurement_type": CtType.STORAGE,
                    "metering_status": CtMeterStatus.NORMAL,
                },
                PhaseNames.PHASE_2: {
                    "eid": 1778385682,
                    "active_power": -3545,
                    "measurement_type": CtType.STORAGE,
                    "metering_status": CtMeterStatus.NORMAL,
                },
            },
        ),
        (
            "8.2.4264_metered_noct",
            "800-00554-r03",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 0,
                "phaseCount": 1,
                "phaseMode": None,
                "consumptionMeter": None,
                "productionMeter": None,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
        (
            "8.2.4345_with_device_data",
            "800-00649-r01",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.ENPOWER
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS
            | SupportedFeatures.DETAILED_INVERTERS,
            {
                "EnvoyDeviceDataInvertersUpdater": SupportedFeatures.INVERTERS
                | SupportedFeatures.DETAILED_INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.ENPOWER,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
            1,
            {
                "ctMeters": 2,
                "phaseCount": 1,
                "phaseMode": EnvoyPhaseMode.THREE,
                "consumptionMeter": CtType.NET_CONSUMPTION,
                "productionMeter": CtType.PRODUCTION,
                "storageMeter": None,
            },
            {},
            {},
            {},
            {},
            {},
            {},
            {},
            {},
        ),
    ],
    ids=[
        "5.0.62",
        "4.10.35",
        "7.3.130",
        "7.3.130_no_consumption",
        "7.3.517",
        "7.3.517_legacy_savings_mode",
        "7.3.517_system_2",
        "7.3.466_metered_disabled_cts",
        "7.6.114_without_cts",
        "7.6.175",
        "7.6.175_total",
        "7.6.175_standard",
        "7.6.175_with_cts",
        "7.6.175_with_cts_3phase",
        "7.3.466_with_cts_3phase",
        "7.6.185_with_cts_and_battery_3t",
        "8.1.41",
        "8.2.127_with_3cts_and_battery_split",
        "8.2.127_with_generator_running",
        "8.2.4286_with_3cts_and_battery_split",
        "8.2.4264_metered_noct",
        "8.2.4345_with_device_data",
    ],
)
@pytest.mark.asyncio
async def test_with_7_x_firmware(
    version: str,
    part_number: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    updaters: dict[str, SupportedFeatures],
    caplog: pytest.LogCaptureFixture,
    phase_count: int,
    common_properties: dict[str, Any],
    production_phases: dict[str, dict[str, Any]],
    consumption_phases: dict[str, dict[str, Any]],
    ct_production: dict[str, Any],
    ct_consumption: dict[str, Any],
    ct_storage: dict[str, Any],
    ct_production_phases: dict[str, dict[str, Any]],
    ct_consumption_phases: dict[str, dict[str, Any]],
    ct_storage_phases: dict[str, dict[str, Any]],
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 7.x firmware."""
    start_7_firmware_mock(mock_aioresponse)
    files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    # get http or https paths based on firmware version
    full_host = endpoint_path(version, envoy.host)
    data = envoy.data
    assert data is not None
    assert data == snapshot

    assert envoy.firmware == version.split("_")[0]
    assert envoy.serial_number

    assert envoy.part_number == part_number
    assert updater_features(envoy._updaters) == updaters
    # We're testing, disable warning on private member
    # pylint: disable=protected-access
    assert envoy._supported_features == supported_features

    # test envoy request methods GET, PUT and POST
    test_data = await load_json_fixture(version, "api_v1_production_inverters")
    mock_aioresponse.post(
        f"{full_host}/api/v1/production/inverters",
        status=200,
        payload=test_data,
        repeat=True,
    )
    mock_aioresponse.put(
        f"{full_host}/api/v1/production/inverters",
        status=200,
        payload=test_data,
        repeat=True,
    )

    # set log level to info 1 time for GET and 1 time for POST to improve COV
    with temporary_log_level("pyenphase", logging.INFO):
        # test request with just an endpoint, should be a GET
        myresponse: aiohttp.ClientResponse = await envoy.request(
            "/api/v1/production/inverters"
        )
        # with data but no method should be post
        # Check that at least one GET request was made to this URL
        cnt, request_data = latest_request(
            mock_aioresponse, "GET", "/api/v1/production/inverters"
        )
        assert cnt > 0
        assert await myresponse.json() == test_data

        # with data but no method should be post
        await envoy.request("/api/v1/production/inverters", data=test_data)
        # Check that at least one POST request was made to this URL
        cnt, request_data = latest_request(
            mock_aioresponse, "POST", "/api/v1/production/inverters"
        )
        assert cnt == 1
        assert orjson.loads(request_data) == test_data

    # with method should be specified method
    caplog.clear()
    await envoy.request("/api/v1/production/inverters", data=test_data, method="PUT")
    cnt, request_data = latest_request(
        mock_aioresponse, "PUT", "/api/v1/production/inverters"
    )
    assert cnt == 1
    assert orjson.loads(request_data) == test_data
    # verify debug log shows correct method
    assert "Sending PUT to" in caplog.text

    # change data to recognize this from previous requests
    caplog.clear()
    test_data.append({"second_post": "test"})  # type: ignore[attr-defined]
    await envoy.request("/api/v1/production/inverters", data=test_data, method="POST")
    # Check that POST requests with changed data was made
    cnt, request_data = latest_request(
        mock_aioresponse, "POST", "/api/v1/production/inverters"
    )
    assert cnt == 1
    assert orjson.loads(request_data) == test_data
    # verify debug log shows correct method
    assert "Sending POST to" in caplog.text
    caplog.clear()

    assert envoy.phase_count == phase_count
    assert envoy.ct_meter_count == common_properties["ctMeters"]
    assert envoy.phase_count == common_properties["phaseCount"]
    assert envoy.phase_mode == common_properties["phaseMode"]
    assert envoy.consumption_meter_type == common_properties["consumptionMeter"]
    assert envoy.production_meter_type == common_properties["productionMeter"]
    assert envoy.storage_meter_type == common_properties["storageMeter"]

    # are CT types represented correctly in model
    assert (str(envoy.storage_meter_type) in envoy.envoy_model) != (
        envoy.storage_meter_type is None
    )
    assert (str(envoy.production_meter_type) in envoy.envoy_model) != (
        envoy.production_meter_type is None
    )
    assert (str(envoy.storage_meter_type) in envoy.envoy_model) != (
        envoy.storage_meter_type is None
    )

    # data is the original collected envoy.data
    # are all production phases reported
    expected_phases = production_phases == {}
    actual_phases = data.system_production_phases is None
    assert not (expected_phases ^ actual_phases)

    # are all consumption phases reported
    expected_phases = consumption_phases == {}
    actual_phases = data.system_consumption_phases is None
    assert not (expected_phases ^ actual_phases)

    reported_phase_count = envoy.active_phase_count
    # are all production phases reported
    expected_phase_count = len(production_phases)
    assert expected_phase_count == reported_phase_count

    # are all consumption phases reported
    expected_phase_count = len(consumption_phases)
    assert expected_phase_count == reported_phase_count

    # Test each production phase
    for phase in production_phases:
        assert data.system_production_phases is not None
        proddata = data.system_production_phases[phase]
        assert proddata is not None
        modeldata = production_phases[phase]

        # test each element of the phase data
        assert proddata.watt_hours_lifetime == modeldata["watt_hours_lifetime"]
        assert proddata.watt_hours_last_7_days == modeldata["watt_hours_last_7_days"]
        assert proddata.watt_hours_today == modeldata["watt_hours_today"]
        assert proddata.watts_now == modeldata["watts_now"]

    # are all consumption phases reported
    assert (
        envoy.active_phase_count == 0
        if data.system_consumption_phases is None
        else len(data.system_consumption_phases)
    )
    # Test each consumption phase
    for phase in consumption_phases:
        assert data.system_consumption_phases is not None
        consdata = data.system_consumption_phases[phase]
        assert consdata is not None
        modeldata = consumption_phases[phase]

        # test each element of the phase data
        assert consdata.watt_hours_lifetime == modeldata["watt_hours_lifetime"]
        assert consdata.watt_hours_last_7_days == modeldata["watt_hours_last_7_days"]
        assert consdata.watt_hours_today == modeldata["watt_hours_today"]
        assert consdata.watts_now == modeldata["watts_now"]

    # test ct production meter values
    for key in ct_production:
        assert data.ctmeter_production is not None
        assert ct_production[key] == getattr(data.ctmeter_production, key)

    # are all CT production phases reported
    assert (
        len(ct_production_phases) == 0
        if data.ctmeter_production_phases is None
        else len(data.ctmeter_production_phases)
    )

    # Test each ct production phase
    for phase in ct_production_phases:
        assert data.ctmeter_production_phases is not None
        ct_proddata = data.ctmeter_production_phases[phase]
        modeldata = ct_production_phases[phase]
        # test each element of the phase data
        for key in modeldata:
            assert modeldata[key] == getattr(ct_proddata, key)

    # test ct consumption meter values
    for key in ct_consumption:
        assert data.ctmeter_consumption is not None
        assert ct_consumption[key] == getattr(data.ctmeter_consumption, key)

    # are all consumption CT phases reported
    assert (
        len(ct_consumption_phases) == 0
        if data.ctmeter_consumption_phases is None
        else len(data.ctmeter_consumption_phases)
    )

    # Test each ct consumption phase
    for phase in ct_consumption_phases:
        assert data.ctmeter_consumption_phases is not None
        ct_consdata = data.ctmeter_consumption_phases[phase]
        modeldata = ct_consumption_phases[phase]
        # test each element of the phase data
        for key in modeldata:
            assert modeldata[key] == getattr(ct_consdata, key)

    # test ct storage meter values
    for key in ct_storage:
        assert data.ctmeter_storage is not None
        assert ct_storage[key] == getattr(data.ctmeter_storage, key)

    # test expected vs actual phases reported
    assert (
        len(ct_storage_phases) == 0
        if data.ctmeter_storage_phases is None
        else len(data.ctmeter_storage_phases)
    )

    # Test each ct storage phase
    for phase in ct_storage_phases:
        assert data.ctmeter_storage_phases is not None
        storedata = data.ctmeter_storage_phases[phase]
        modeldata = ct_storage_phases[phase]
        # test each element of the phase data
        for key in modeldata:
            assert modeldata[key] == getattr(storedata, key)

    # COV test with no production segment
    if "production" in files:
        try:
            json_data = await load_json_fixture(version, "production")
        except json.decoder.JSONDecodeError:
            json_data = None
        if json_data:
            del json_data["production"]
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/production",
            status=200,
            payload=json_data,
        )
    else:
        override_mock(mock_aioresponse, "get", f"{full_host}/production", status=404)
    with contextlib.suppress(EnvoyProbeFailed):
        await envoy.probe()

    # test inverter device data with missing data fields
    if "ivp_pdm_device_data" in files:
        # rebuild default data setup
        files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        await envoy.probe()

        # verify we have inverter and inverter details details
        assert envoy.supported_features & (
            SupportedFeatures.DETAILED_INVERTERS | SupportedFeatures.INVERTERS
        )
        json_data = await load_json_fixture(version, "ivp_pdm_device_data")

        # remove channels from first inverter, should cause switch to production inverter data
        for key in json_data:
            if key not in ("deviceCount", "deviceDataLimit"):
                del json_data[key]["channels"]
                break

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/pdm/device_data",
            status=200,
            payload=json_data,
        )
        await envoy.probe()
        # verify we have production inverter data only
        assert envoy.supported_features & SupportedFeatures.INVERTERS
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].ac_frequency is None

        # rebuild default data setup
        files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        await envoy.probe()

        # verify we have inverter and inverter details details
        assert envoy.supported_features & (
            SupportedFeatures.DETAILED_INVERTERS | SupportedFeatures.INVERTERS
        )
        json_data = await load_json_fixture(version, "ivp_pdm_device_data")

        # remove lastReading from first inverter channel, should cause switch to production inverter data
        for key in json_data:
            if key not in ("deviceCount", "deviceDataLimit"):
                del json_data[key]["channels"][0]["lastReading"]
                break

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/pdm/device_data",
            status=200,
            payload=json_data,
        )
        await envoy.probe()
        # verify we have production inverter data only
        assert envoy.supported_features & SupportedFeatures.INVERTERS
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].ac_frequency is None

        # rebuild default data setup
        files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        await envoy.probe()

        # verify we have inverter and inverter details
        assert envoy.supported_features & (
            SupportedFeatures.DETAILED_INVERTERS | SupportedFeatures.INVERTERS
        )
        json_data = await load_json_fixture(version, "ivp_pdm_device_data")

        # set deviceCount equal to deviceDataLimit, should cause switch to production inverter data
        json_data["deviceCount"] = json_data["deviceDataLimit"]

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/pdm/device_data",
            status=200,
            payload=json_data,
        )
        await envoy.probe()
        # verify we have production inverter data only
        assert envoy.supported_features & SupportedFeatures.INVERTERS
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].ac_frequency is None

        # rebuild default data setup
        files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        await envoy.probe()

        # verify we have inverter and inverter details
        assert envoy.supported_features & (
            SupportedFeatures.DETAILED_INVERTERS | SupportedFeatures.INVERTERS
        )
        json_data = await load_json_fixture(version, "ivp_pdm_device_data")

        # set deviceCount equal to deviceDataLimit, should cause switch to production inverter data
        json_data["deviceCount"] = json_data["deviceDataLimit"]

        # remove deviceCount key, should cause switch to production inverter data
        del json_data["deviceCount"]

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/pdm/device_data",
            status=200,
            payload=json_data,
        )
        await envoy.probe()
        # verify we have production inverter data only
        assert envoy.supported_features & SupportedFeatures.INVERTERS
        assert not (envoy.supported_features & SupportedFeatures.DETAILED_INVERTERS)
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].ac_frequency is None

        # rebuild default data setup
        files = await prep_envoy(mock_aioresponse, "127.0.0.1", version)
        await envoy.probe()

        # verify we have inverter and inverter details details
        assert envoy.supported_features & (
            SupportedFeatures.DETAILED_INVERTERS | SupportedFeatures.INVERTERS
        )
        json_data = await load_json_fixture(version, "ivp_pdm_device_data")

        # remove lifetime from first channel of inverters, should cause lifetime to be None
        for key in json_data:
            if key not in ("deviceCount", "deviceDataLimit"):
                del json_data[key]["channels"][0]["lifetime"]

        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/pdm/device_data",
            status=200,
            payload=json_data,
            repeat=2,
        )
        await envoy.probe()
        # verify we have still have inverter details
        assert (
            envoy.supported_features & SupportedFeatures.INVERTERS
            | SupportedFeatures.INVERTERS
        )
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].lifetime_energy is None
            assert data.inverters[key].last_report_watts is not None

    else:
        override_mock(
            mock_aioresponse, "get", f"{full_host}/ivp/pdm/device_data", status=404
        )
        await envoy.probe()
        data = await envoy.update()
        for key in data.inverters:
            assert data.inverters[key].ac_frequency is None
