"""Model for a standby generator connected to the Enpower/IQ System Controller."""

# Data Source: URL_GENERATOR (status), URL_GEN_CONFIG (configuration)
# & URL_GEN_SCHEDULE (schedule)

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class EnvoyGenerator:
    """Model for the generator status."""

    admin_state: str
    oper_state: str
    admin_mode: int
    schedule: int
    start_soc: int
    stop_soc: int
    exc_on: int
    present: bool
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

    max_cont_gen_amps: float
    min_gen_loading_perc: int
    max_gen_efficiency_perc: int
    name_plate_rating_wat: float
    start_method: str
    warm_up_mins: int
    cool_down_mins: int
    gen_type: str
    model: str
    manufacturer: str
    last_updated_by: str
    generator_id: str
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
