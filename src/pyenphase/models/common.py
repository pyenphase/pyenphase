"""Model for common properties of an envoy."""

from dataclasses import dataclass, field

from ..models.meters import CtType, EnvoyPhaseMode


@dataclass(slots=True)
class CommonProperties:
    """
    Model for common properties of an envoy shared amongst all updaters.

    One set are properties set during probe to share amongst updaters
    and with clients. These should be reset at each probe run.

    More properties can be added, originators should handle reset as needed
    by adding to reset_probe_properties to reset at probe or in a different way
    or leave existing all lifetime.
    """

    # probe properties here, also add to reset_probe_properties
    # shared amongst production updaters, needs reset before probe
    production_fallback_list: list[str] = field(
        default_factory=list[str]
    )  #: Fallback production endpoints for Metered without CT

    #: ACB batteries report current power in production and in ensemble secctl
    #: Ensemble updater should only report combined ACB en Encharge if production report has data
    acb_batteries_reported: int = 0

    #: imeter flag from /info. If true envoy is metered type
    #: used to detect metered without actual CT installed to enable picking correct data
    imeter_info: bool = False

    # other properties from here, reset by originator

    # controlled by meters updater
    phase_count: int = 0  #: number of phases configured in envoy
    ct_meter_count: int = 0  #: number of active ct meters
    phase_mode: EnvoyPhaseMode | None = None  #: phase mode configured in the CT meters
    consumption_meter_type: CtType | None = (
        None  #: What type of consumption meter is installed, if installed
    )
    production_meter_type: CtType | None = (
        None  #: What type of production meter is installed, if installed
    )
    storage_meter_type: CtType | None = (
        None  #: What type of storage meter is installed, if installed
    )
    # controlled by production updater
    active_phase_count: int = 0  #: number of phases actually reporting phase data

    # controlled by
    # none_probe_property: str = "hello world" #: test

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
