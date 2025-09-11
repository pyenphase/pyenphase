"""Model for common properties of an envoy."""

from dataclasses import dataclass, field

from ..models.meters import EnvoyPhaseMode


@dataclass(slots=True)
class CommonProperties:
    """
    Model for common properties for EnvoyUpdater class updaters.

    Class :class:`EnvoyUpdater` implementations
    each collect a specific data set or information that can be provided by
    an Envoy. Depending on the actual model, firmware, and installed
    an Envoy may need one or more updaters to provide all data
    components, for :any:`pyenphase.Envoy.update`.

    Although each updater has its specific scope, some may need to share
    information or make operational information available. One set of
    properties are used during probe to share amongst updaters and with
    client applications. These should be reset at each probe run. A second
    set of properties are specific for an updater during its runtime. The
    updater is in control of resetting the property as needed.
    """

    # probe properties here, also add to reset_probe_properties
    # shared amongst production updaters, needs reset before probe
    #: Probe property, Fallback production endpoints for Metered without CT.
    #: Solar production data has to be collected from different
    #: sources in the Envoy, depending on actual Envoy configuration,
    #: each utilizing a different updater. This list will be filled
    #: with candidate updaters to use.
    production_fallback_list: list[str] = field(
        default_factory=list
    )  #: Fallback production endpoints for Metered without CT

    #: ACB batteries report current power in production and in the Ensemble SECCTRL endpoint
    #: The Ensemble updater should only report combined ACB and Encharge if production reported data
    acb_batteries_reported: int = 0

    #: imeter flag from /info. If true envoy is metered type
    #: used to detect metered without actual CT installed to enable picking correct data
    imeter_info: bool = False

    # other properties from here, reset by originator

    # controlled by meters updater
    #: meters updater, number of phases configured in envoy
    phase_count: int = 0
    #: meters updater, number of active ct meters
    ct_meter_count: int = 0
    #: meters updater, phase mode configured in the CT meters
    phase_mode: EnvoyPhaseMode | None = None
    #: meters updater, list of installed meter types, if installed
    meter_types: list[str] = field(default_factory=list)
    #: production updater, number of phases actually reporting phase data
    active_phase_count: int = 0

    def reset_probe_properties(self, is_metered: bool = False) -> None:
        """
        Reset common properties at start of probe.

        Probe common properties are reset at each probe by :any:`Envoy.probe`
        to avoid sticking values. This should only be done for common properties
        shared among updaters. Any common properties set outside of probe or controlled
        by a specific updater, should be reset at different moments by the
        owner of the property.

        Shared common properties to reset:

            - production_fallback_list shared amongst production updaters
            - ACB_batteries_reported shared between production and Ensemble
            - imeter_info setting from /info indicating envoy is metered type

        :return: None
        """
        # shared amongst production updaters
        self.production_fallback_list = []
        self.imeter_info = is_metered

        # shared between production and ensemble
        self.acb_batteries_reported = 0
