"""Test endpoint for envoy v7 and newer firmware"""

import asyncio
import logging
from dataclasses import replace
from typing import Any

import aiohttp
import orjson
import pytest
from aiohttp.client_reqrep import ConnectionKey
from aioresponses import aioresponses
from syrupy.assertion import SnapshotAssertion

from pyenphase.const import (
    URL_DRY_CONTACT_SETTINGS,
    URL_DRY_CONTACT_STATUS,
    URL_ENSEMBLE_INVENTORY,
    URL_GRID_RELAY,
    URL_TARIFF,
)
from pyenphase.envoy import SupportedFeatures
from pyenphase.exceptions import EnvoyError, EnvoyFeatureNotAvailable
from pyenphase.models.dry_contacts import DryContactStatus
from pyenphase.models.tariff import EnvoyStorageMode

from .common import (
    endpoint_path,
    get_mock_envoy,
    latest_request,
    load_json_fixture,
    override_mock,
    prep_envoy,
    start_7_firmware_mock,
    updater_features,
)

LOGGER = logging.getLogger(__name__)


@pytest.mark.parametrize(
    (
        "version",
        "supported_features",
        "updaters",
    ),
    [
        (
            "5.0.62",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
        ),
        (
            "4.10.35",
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
        ),
        (
            "7.3.130",
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
        ),
        (
            "7.3.130_no_consumption",
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
        ),
        (
            "7.3.517",
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
        ),
        (
            "7.3.517_legacy_savings_mode",
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
        ),
        (
            "7.3.517_system_2",
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
        ),
        (
            "7.3.466_metered_disabled_cts",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
        ),
        (
            "7.6.114_without_cts",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175_total",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
        ),
        (
            "7.6.175_standard",
            SupportedFeatures.INVERTERS | SupportedFeatures.PRODUCTION,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyApiV1ProductionUpdater": SupportedFeatures.PRODUCTION,
            },
        ),
        (
            "7.6.175_with_cts",
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
        ),
        (
            "7.6.175_with_cts_3phase",
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
        ),
        (
            "7.3.466_with_cts_3phase",
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
        ),
        (
            "7.6.185_with_cts_and_battery_3t",
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
        ),
        (
            "8.1.41",
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
        ),
        (
            "8.2.127_with_3cts_and_battery_split",
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
        ),
        (
            "8.2.127_with_generator_running",
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
        ),
        (
            "8.2.4286_with_3cts_and_battery_split",
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
        ),
        (
            "8.2.4264_metered_noct",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyProductionJsonFallbackUpdater": SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
        ),
        (
            "8.2.4345_with_device_data",
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
        ),
        (
            "8.3.1598_collar",
            SupportedFeatures.INVERTERS
            | SupportedFeatures.METERING
            | SupportedFeatures.TOTAL_CONSUMPTION
            | SupportedFeatures.NET_CONSUMPTION
            | SupportedFeatures.ENCHARGE
            | SupportedFeatures.DUALPHASE
            | SupportedFeatures.PRODUCTION
            | SupportedFeatures.TARIFF
            | SupportedFeatures.CTMETERS
            | SupportedFeatures.COLLAR
            | SupportedFeatures.C6CC,
            {
                "EnvoyApiV1ProductionInvertersUpdater": SupportedFeatures.INVERTERS,
                "EnvoyEnembleUpdater": SupportedFeatures.ENCHARGE
                | SupportedFeatures.COLLAR
                | SupportedFeatures.C6CC,
                "EnvoyMetersUpdater": SupportedFeatures.CTMETERS
                | SupportedFeatures.DUALPHASE,
                "EnvoyProductionJsonUpdater": SupportedFeatures.METERING
                | SupportedFeatures.TOTAL_CONSUMPTION
                | SupportedFeatures.NET_CONSUMPTION
                | SupportedFeatures.PRODUCTION,
                "EnvoyTariffUpdater": SupportedFeatures.TARIFF,
            },
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
        "8.3.1598_collar",
    ],
)
@pytest.mark.asyncio
async def test_with_7_x_firmware(
    version: str,
    snapshot: SnapshotAssertion,
    supported_features: SupportedFeatures,
    updaters: dict[str, SupportedFeatures],
    caplog: pytest.LogCaptureFixture,
    mock_aioresponse: aioresponses,
    test_client_session: aiohttp.ClientSession,
) -> None:
    """Verify with 7.x firmware."""
    start_7_firmware_mock(mock_aioresponse)
    await prep_envoy(mock_aioresponse, "127.0.0.1", version)
    caplog.set_level(logging.DEBUG)

    envoy = await get_mock_envoy(test_client_session)
    # get http or https paths based on firmware version
    full_host = endpoint_path(version, envoy.host)
    data = envoy.data
    assert data is not None
    assert data == snapshot

    assert updater_features(envoy._updaters) == updaters
    # We're testing, disable warning on private member
    # pylint: disable=protected-access
    assert envoy._supported_features == supported_features

    # Test enpower
    if supported_features & supported_features.ENPOWER:
        # switch off debug for one post to improve COV
        mock_aioresponse.post(
            f"{full_host}{URL_GRID_RELAY}", status=200, payload={}, repeat=True
        )
        await envoy.go_on_grid()
        # Get the last POST request to grid relay
        cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GRID_RELAY)
        assert orjson.loads(request_data) == {"mains_admin_state": "closed"}

        await envoy.go_off_grid()
        cnt, request_data = latest_request(mock_aioresponse, "POST", URL_GRID_RELAY)
        assert orjson.loads(request_data) == {"mains_admin_state": "open"}

        # Test updating dry contacts
        with pytest.raises(ValueError):
            await envoy.update_dry_contact({"missing": "id"})

        # updating dry contacts before first data update should fail
        with pytest.raises(ValueError):
            bad_envoy = await get_mock_envoy(test_client_session, update=False)
            await bad_envoy.probe()
            await bad_envoy.update_dry_contact({"id": "NC1"})

        assert data.dry_contact_settings is not None
        dry_contact = data.dry_contact_settings["NC1"]
        new_data: dict[str, Any] = {"id": "NC1", "load_name": "NC1 Test"}
        new_model = replace(dry_contact, **new_data)

        await envoy.update_dry_contact(new_data)
        cnt, request_data = latest_request(
            mock_aioresponse, "POST", URL_DRY_CONTACT_SETTINGS
        )
        assert orjson.loads(request_data) == {"dry_contacts": new_model.to_api()}

        if data.dry_contact_settings["NC1"].black_start is not None:
            assert (
                new_model.to_api()["black_s_start"]
                == data.dry_contact_settings["NC1"].black_start
            )
        else:
            assert "black_s_start" not in new_model.to_api()

        await envoy.open_dry_contact("NC1")
        assert data.dry_contact_status is not None
        assert data.dry_contact_status["NC1"].status == DryContactStatus.OPEN
        # Get the last POST request to dry contact status
        cnt, request_data = latest_request(
            mock_aioresponse, "POST", URL_DRY_CONTACT_STATUS
        )
        assert orjson.loads(request_data) == {
            "dry_contacts": {"id": "NC1", "status": "open"}
        }

        await envoy.close_dry_contact("NC1")
        assert data.dry_contact_status["NC1"].status == DryContactStatus.CLOSED
        cnt, request_data = latest_request(
            mock_aioresponse, "POST", URL_DRY_CONTACT_STATUS
        )
        assert orjson.loads(request_data) == {
            "dry_contacts": {"id": "NC1", "status": "closed"}
        }

        assert "Sending POST" in caplog.text

        # test error returned by action methods calling _json_request
        override_mock(
            mock_aioresponse,
            "post",
            f"{full_host}{URL_GRID_RELAY}",
            status=300,
            payload={},
            repeat=2,
        )
        with pytest.raises(EnvoyError):
            await envoy.go_on_grid()
        with pytest.raises(EnvoyError):
            await envoy.go_off_grid()

        override_mock(
            mock_aioresponse,
            "post",
            f"{full_host}{URL_GRID_RELAY}",
            exception=aiohttp.ClientError("Test Connection error"),
        )
        with pytest.raises(EnvoyError):
            await envoy.go_on_grid()
        mock_aioresponse.post(
            f"{full_host}{URL_GRID_RELAY}",
            exception=asyncio.TimeoutError("Test timeout exception"),
        )
        with pytest.raises(EnvoyError):
            await envoy.go_off_grid()

        override_mock(
            mock_aioresponse,
            "post",
            f"{full_host}{URL_DRY_CONTACT_SETTINGS}",
            status=300,
            payload={},
        )
        with pytest.raises(EnvoyError):
            await envoy.update_dry_contact(new_data)

        override_mock(
            mock_aioresponse,
            "post",
            f"{full_host}{URL_DRY_CONTACT_STATUS}",
            exception=aiohttp.ClientError("Test Connection error"),
        )
        with pytest.raises(EnvoyError):
            await envoy.close_dry_contact("NC1")

        mock_aioresponse.post(
            f"{full_host}{URL_DRY_CONTACT_STATUS}",
            exception=asyncio.TimeoutError("Test timeout exception"),
        )
        with pytest.raises(EnvoyError):
            await envoy.open_dry_contact("NC1")

    else:
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.go_off_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.go_on_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.update_dry_contact({"id": "NC1"})
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.update_dry_contact({"id": "NC1"})
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.open_dry_contact("NC1")
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.close_dry_contact("NC1")

    if supported_features & SupportedFeatures.GENERATOR:
        # COV ensemble ENDPOINT_PROBE_EXCEPTIONS
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/ss/gen_config",
            status=500,
            payload=await load_json_fixture(version, "ivp_ss_gen_config"),
        )
        await envoy.probe()
        # restore from prior changes
        mock_aioresponse.get(
            f"{full_host}/ivp/ss/gen_config",
            status=200,
            payload=await load_json_fixture(version, "ivp_ss_gen_config"),
            repeat=True,
        )
        await envoy.probe()

    if (supported_features & SupportedFeatures.ENCHARGE) and (
        supported_features & SupportedFeatures.TARIFF
    ):
        # Test `savings-mode` is converted to `economy`
        assert data.raw is not None
        if data.raw[URL_TARIFF]["tariff"]["storage_settings"]["mode"] == "savings-mode":
            assert data.tariff is not None
            assert data.tariff.storage_settings is not None
            assert data.tariff.storage_settings.mode == EnvoyStorageMode.SAVINGS

        assert data.tariff is not None
        assert data.tariff.storage_settings is not None
        storage_settings = data.tariff.storage_settings
        new_data = {"charge_from_grid": True}
        new_storage_model = replace(storage_settings, **new_data)

        if data.tariff.storage_settings.date is not None:
            assert (
                new_storage_model.to_api()["date"] == data.tariff.storage_settings.date
            )
        else:
            assert "date" not in new_storage_model.to_api()

        if data.tariff.storage_settings.opt_schedules is not None:
            assert (
                new_storage_model.to_api()["opt_schedules"]
                == data.tariff.storage_settings.opt_schedules
            )
        else:
            assert "opt_schedules" not in new_storage_model.to_api()

        # Test setting battery features
        await envoy.enable_charge_from_grid()
        assert data.tariff.storage_settings.charge_from_grid is True
        cnt, request_data = latest_request(mock_aioresponse, "PUT", URL_TARIFF)
        assert orjson.loads(request_data) == {"tariff": data.tariff.to_api()}

        await envoy.disable_charge_from_grid()
        assert not bool(data.tariff.storage_settings.charge_from_grid)
        cnt, request_data = latest_request(mock_aioresponse, "PUT", URL_TARIFF)
        assert orjson.loads(request_data) == {"tariff": data.tariff.to_api()}

        await envoy.set_reserve_soc(50)
        assert data.tariff.storage_settings.reserved_soc == round(float(50), 1)
        cnt, request_data = latest_request(mock_aioresponse, "PUT", URL_TARIFF)
        assert orjson.loads(request_data) == {"tariff": data.tariff.to_api()}

        await envoy.set_storage_mode(EnvoyStorageMode.SELF_CONSUMPTION)
        assert data.tariff.storage_settings.mode == EnvoyStorageMode.SELF_CONSUMPTION
        cnt, request_data = latest_request(mock_aioresponse, "PUT", URL_TARIFF)
        assert orjson.loads(request_data) == {"tariff": data.tariff.to_api()}

        with pytest.raises(TypeError):
            await envoy.set_storage_mode("invalid")  # type: ignore[arg-type]

        # test error returned by action methods calling _json_request
        override_mock(
            mock_aioresponse,
            "put",
            f"{full_host}{URL_TARIFF}",
            status=300,
            payload={},
        )
        with pytest.raises(EnvoyError):
            await envoy.enable_charge_from_grid()
        mock_aioresponse.put(
            f"{full_host}{URL_TARIFF}",
            exception=asyncio.TimeoutError("Test timeout exception"),
        )
        with pytest.raises(EnvoyError):
            await envoy.disable_charge_from_grid()
        mock_aioresponse.put(
            f"{full_host}{URL_TARIFF}",
            exception=aiohttp.ClientConnectorError(
                connection_key=ConnectionKey(
                    host="127.0.0.1",
                    port=443,
                    is_ssl=True,
                    ssl=False,
                    proxy=None,
                    proxy_auth=None,
                    proxy_headers_hash=None,
                ),
                os_error=OSError("Test Connection error"),
            ),
        )
        with pytest.raises(EnvoyError):
            await envoy.set_storage_mode(EnvoyStorageMode.SELF_CONSUMPTION)
        mock_aioresponse.put(
            f"{full_host}{URL_TARIFF}",
            exception=aiohttp.ClientConnectorError(
                connection_key=ConnectionKey(
                    host="127.0.0.1",
                    port=443,
                    is_ssl=True,
                    ssl=False,
                    proxy=None,
                    proxy_auth=None,
                    proxy_headers_hash=None,
                ),
                os_error=OSError("Test Connection error"),
            ),
        )
        with pytest.raises(EnvoyError):
            await envoy.set_reserve_soc(50)

        # test correct handling if storage_settings mode = None
        # should result no longer throw Valueerror but result in None value
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        json_data["tariff"]["storage_settings"]["mode"] = None
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/admin/lib/tariff",
            status=200,
            payload=json_data,
        )
        await envoy.update()
        data = envoy.data
        assert data is not None
        assert data.tariff is not None
        assert data.tariff.storage_settings is not None
        assert data.tariff.storage_settings.mode is None

        # COV test with missing logger
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        del json_data["tariff"]["logger"]
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/admin/lib/tariff",
            status=200,
            payload=json_data,
        )
        override_mock(
            mock_aioresponse,
            "put",
            f"{full_host}/admin/lib/tariff",
            status=200,
            payload=json_data,
        )
        await envoy.update()
        data = envoy.data
        assert data is not None
        assert data.tariff is not None
        data.tariff.to_api()

        # COV test with missing date for tariff and storage settings
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        del json_data["tariff"]["date"]
        del json_data["tariff"]["storage_settings"]["date"]
        mock_aioresponse.get(
            f"{full_host}/admin/lib/tariff", status=200, payload=json_data
        )
        mock_aioresponse.put(
            f"{full_host}/admin/lib/tariff", status=200, payload=json_data
        )
        await envoy.update()
        data = envoy.data
        assert data is not None
        assert data.tariff is not None
        data.tariff.to_api()

        # COV test with missing storage settings
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        del json_data["tariff"]["storage_settings"]
        mock_aioresponse.get(
            f"{full_host}/admin/lib/tariff", status=200, payload=json_data
        )
        mock_aioresponse.put(
            f"{full_host}/admin/lib/tariff", status=200, payload=json_data
        )
        await envoy.update()
        data = envoy.data
        assert data is not None
        assert data.tariff is not None
        data.tariff.to_api()

        # COV test with error in result
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        json_data.update({"error": "error"})
        mock_aioresponse.get(
            f"{full_host}/admin/lib/tariff", status=200, payload=json_data
        )
        try:
            await envoy.probe()
        except AttributeError:
            assert "No tariff data found" in caplog.text

        # COV test with no enpower features
        json_data = await load_json_fixture(version, "ivp_ensemble_inventory")
        json_data[0]["type"] = "NOEXCHARGE"  # type: ignore[index]
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/ensemble/inventory",
            status=200,
            payload=json_data,
            repeat=2,
        )
        await envoy.probe()
        await envoy.update()

        # COV ensemble ENDPOINT_PROBE_EXCEPTIONS
        mock_aioresponse.get(
            f"{full_host}/ivp/ensemble/inventory",
            status=500,
            payload=await load_json_fixture(version, "ivp_ensemble_inventory"),
        )
        await envoy.probe()

        # restore from prior changes
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/ivp/ensemble/inventory",
            status=200,
            payload=await load_json_fixture(version, "ivp_ensemble_inventory"),
            repeat=True,
        )
        json_data = await load_json_fixture(version, "admin_lib_tariff")
        override_mock(
            mock_aioresponse,
            "get",
            f"{full_host}/admin/lib/tariff",
            status=200,
            payload=json_data,
            repeat=True,
        )

        bad_envoy = await get_mock_envoy(test_client_session)
        await bad_envoy.probe()
        with pytest.raises(EnvoyFeatureNotAvailable):
            assert bad_envoy.data is not None
            assert bad_envoy.data.tariff is not None
            bad_envoy.data.tariff.storage_settings = None
            await bad_envoy.enable_charge_from_grid()
        with pytest.raises(ValueError):
            assert bad_envoy.data is not None
            bad_envoy.data.tariff = None
            await bad_envoy.enable_charge_from_grid()
        with pytest.raises(ValueError):
            bad_envoy.data = None
            await bad_envoy.enable_charge_from_grid()
    else:
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.enable_charge_from_grid()
        with pytest.raises(EnvoyFeatureNotAvailable):
            await envoy.disable_charge_from_grid()

    if supported_features & SupportedFeatures.COLLAR:
        # Test collar data
        assert data.collar is not None
        assert data.raw is not None
        assert data.raw[URL_ENSEMBLE_INVENTORY]
        collar_raw = data.raw[URL_ENSEMBLE_INVENTORY]
        collar = [
            collar_type["devices"]
            for collar_type in collar_raw
            if collar_type["type"] == "COLLAR"
        ]
        assert collar
        #  should be 1 type collar only
        assert len(collar) == 1
        # should be only 1 collar entry in list
        assert len(collar[0]) == 1
        # verify model field value matches raw data value
        assert data.collar.serial_number == collar[0][0]["serial_num"]
        assert data.collar.admin_state_str == collar[0][0]["admin_state_str"]
        assert data.collar.mid_state == collar[0][0]["mid_state"]
        assert data.collar.grid_state == collar[0][0]["grid_state"]
        assert data.collar.collar_state == collar[0][0]["collar_state"]
    else:
        assert data.collar is None

    if supported_features & SupportedFeatures.C6CC:
        # Test combiner data
        assert data.c6cc is not None
        assert data.raw is not None
        assert data.raw[URL_ENSEMBLE_INVENTORY]
        c6cc_raw = data.raw[URL_ENSEMBLE_INVENTORY]
        c6cc = [
            c6cc_type["devices"]
            for c6cc_type in c6cc_raw
            if c6cc_type["type"] == "C6 COMBINER CONTROLLER"
        ]
        assert c6cc
        #  should be 1 type collar only
        assert len(c6cc) == 1
        # should be only 1 collar entry in list
        assert len(c6cc[0]) == 1
        # verify model field value matches raw data value
        assert data.c6cc.admin_state_str == c6cc[0][0]["admin_state_str"]
        assert data.c6cc.serial_number == c6cc[0][0]["serial_num"]
    else:
        assert data.c6cc is None
