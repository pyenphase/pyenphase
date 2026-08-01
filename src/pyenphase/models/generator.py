"""Model for a standby generator connected to the Enpower/IQ System Controller."""

# Data Source: URL_GENERATOR (status), URL_GEN_CONFIG (configuration),
# URL_GEN_SCHEDULE (schedule) & URL_GEN_MODE (operation mode)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyGenerator:
    """Model for the generator status."""

    #: Administrative state of the generator relay, e.g. "open" or "closed"
    admin_state: str
    #: Operational state of the generator relay, e.g. "open" or "closed"
    oper_state: str
    #: Configured generator operation mode as a numeric code
    admin_mode: int
    #: Whether an exercise schedule is active
    schedule: int
    #: Battery state of charge at which the generator starts
    start_soc: int
    #: Battery state of charge at which the generator stops
    stop_soc: int
    #: Whether a generator exercise run is currently active
    exc_on: int
    #: Whether a generator is present in the system
    present: bool
    #: Generator type as a numeric code
    type: int

    @classmethod
    def from_api(cls, generator: dict[str, Any]) -> EnvoyGenerator:
        """Initialize from the API."""
        return cls(
            admin_state=generator["admin_state"],
            oper_state=generator["oper_state"],
            admin_mode=generator["admin_mode"],
            schedule=generator["schedule"],
            start_soc=generator["start_soc"],
            stop_soc=generator["stop_soc"],
            exc_on=generator["exc_on"],
            present=bool(generator["present"]),
            type=generator["type"],
        )


@dataclass(slots=True)
class EnvoyGeneratorConfig:
    """Model for the generator configuration."""

    #: Maximum continuous generator output current in amps
    max_cont_gen_amps: float
    #: Minimum generator loading as a percentage of its rating
    min_gen_loading_perc: int
    #: Maximum generator efficiency as a percentage
    max_gen_efficiency_perc: int
    #: Generator name plate power rating, as reported by the Envoy
    name_plate_rating_wat: float
    #: How the generator is started, e.g. "auto" for two-wire start
    start_method: str
    #: Generator warm-up time in minutes
    warm_up_mins: int
    #: Generator cool-down time in minutes
    cool_down_mins: int
    #: Generator type, e.g. "Standby"
    gen_type: str
    #: Generator model as configured at installation
    model: str
    #: Generator manufacturer as configured at installation
    manufacturer: str
    #: Source of the last configuration update
    last_updated_by: str
    #: Generator identification as configured at installation
    generator_id: str
    #: Whether batteries may be charged from the generator
    charge_from_generator: bool

    @classmethod
    def from_api(cls, config: dict[str, Any]) -> EnvoyGeneratorConfig:
        """Initialize from the API."""
        return cls(
            max_cont_gen_amps=config["max_cont_gen_amps"],
            min_gen_loading_perc=config["min_gen_loading_perc"],
            max_gen_efficiency_perc=config["max_gen_efficiency_perc"],
            name_plate_rating_wat=config["name_plate_rating_wat"],
            start_method=config["start_method"],
            warm_up_mins=config["warm_up_mins"],
            cool_down_mins=config["cool_down_mins"],
            gen_type=config["gen_type"],
            model=config["model"],
            manufacturer=config["manufacturer"],
            last_updated_by=config["last_updated_by"],
            generator_id=config["generator_id"],
            charge_from_generator=config["charge_from_generator"],
        )


@dataclass(slots=True)
class EnvoyGeneratorMode:
    """Model for the generator operation mode."""

    #: Requested generator mode, one of "off", "on" or "auto"
    gen_cmd: str
    last_updated_by: str

    @classmethod
    def from_api(cls, mode: dict[str, Any]) -> EnvoyGeneratorMode:
        """Initialize from the API."""
        return cls(
            gen_cmd=mode["gen_cmd"],
            last_updated_by=mode["last_updated_by"],
        )


@dataclass(slots=True)
class EnvoyGeneratorSchedule:
    """Model for the generator exercise and state-of-charge schedule."""

    #: Exercise interval in weeks
    exercise_freq_in_weeks: int
    #: Exercise start time in minutes after midnight
    exercise_start: int
    #: Exercise duration in minutes
    exercise_duration: int
    #: Day of the week the exercise runs on
    exercise_day: str
    default_start_soc: int
    default_stop_soc: int
    last_updated_by: str

    @classmethod
    def from_api(cls, schedule: dict[str, Any]) -> EnvoyGeneratorSchedule:
        """Initialize from the API."""
        exercise_config = schedule["exercise_config"]
        default_soc = schedule["default_soc"]
        return cls(
            exercise_freq_in_weeks=exercise_config["freq_in_weeks"],
            exercise_start=exercise_config["start"],
            exercise_duration=exercise_config["duration"],
            exercise_day=exercise_config["day"],
            default_start_soc=default_soc["start_soc"],
            default_stop_soc=default_soc["stop_soc"],
            last_updated_by=schedule["last_updated_by"],
        )
