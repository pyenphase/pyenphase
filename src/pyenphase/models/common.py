"""Model for common properties of an envoy."""

from dataclasses import dataclass, field

from ..models.meters import CtType, EnvoyPhaseMode


@dataclass(slots=True)
class CommonProperties:
    """
    Model for common properties for EnvoyUpdater class updaters.

    Class :any:`EnvoyUpdater` updaters each collect a specific data set
    or information that can be provided by an Envoy. Depending on actual
    make, firmware and installed components an actual Envoy will need
    1 or more updater to provide all data for :any:`Envoy.update`.

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

    #: ACB batteries report current power in production and in ensemble secctl
    #: Ensemble updater should only report combined ACB en Encharge if production report has data
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
    #: meters updater, what type of consumption meter is installed, if installed
    consumption_meter_type: CtType | None = None
    #: meters updater, what type of production meter is installed, if installed
    production_meter_type: CtType | None = None
    #: meters updater, what type of storage meter is installed, if installed
    storage_meter_type: CtType | None = None

    # controlled by production updater
    #: production updater, number of phases actually reporting phase data
    active_phase_count: int = 0

    # controlled by xyz updater
    #: xyz updater, none_probe_property: str = "hello world" #: test

    def reset_probe_properties(self, is_metered: bool = False) -> None:
        """
        Reset common properties that are initialized during probe.

        probe properties are reset at each probe to avoid sticking memories.
        This should exclude common properties set outside of probe
        or controlled by a specific updater, these should be reset at
        different moments by different method by updaters or owner

        reset properties:

            production_fallback_list shared amongst production updaters
            ACB_batteries_reported shared between production and Ensemble
            imeter_info setting from /info indicating envoy is metered type
        """
        # shared amongst production updaters
        self.production_fallback_list = []
        self.imeter_info = is_metered

        # shared between production and ensemble
        self.acb_batteries_reported = 0

        # shared by
