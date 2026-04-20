import pathlib
import numpy as np
import pandas as pd
import fitdecode


def _convert_fit_coords_to_deg(coord):
    """Convert semicircle 32-bit integer coordinate to degrees"""
    return coord * (180 / 2**31)


def _generate_frame_from_fit(fit_file: pathlib.Path, selected_frames: list):
    with fitdecode.FitReader(fit_file, check_crc=False) as fit:
        for frame in fit:
            if (
                frame.frame_type == fitdecode.FIT_FRAME_DATA
                and frame.name in selected_frames
            ):
                yield frame


def _extract_str(frame, field_name: str):
    if frame.has_field(field_name) and frame.get_value(field_name) is not None:
        return frame.get_value(field_name)
    return None


def _extract_value(frame, field_name: str, datatype):
    if frame.has_field(field_name) and frame.get_value(field_name) is not None:

        return datatype(frame.get_value(field_name))
    return 0 if datatype is int else np.nan


def get_sport_from_fit(fit_content) -> str:
    for frame in _generate_frame_from_fit(fit_content, ["session"]):
        return _extract_str(frame, "sport")
    return None


def extract_fit(file_path: pathlib.Path) -> pd.DataFrame:
    lap_number = 1
    laps = []
    times = []
    lats = []
    lons = []
    eles = []
    dists = []
    speeds = []
    hrs = []
    cads = []

    for frame in _generate_frame_from_fit(file_path, ["lap", "record", "session"]):
        if frame.name == "record":
            laps.append(lap_number)
            times.append(_extract_str(frame, "timestamp"))
            lats.append(_extract_value(frame, "position_lat", float))
            lons.append(_extract_value(frame, "position_long", float))
            eles.append(_extract_value(frame, "altitude", float))
            dists.append(_extract_value(frame, "distance", float))
            speeds.append(_extract_value(frame, "speed", float))
            hrs.append(_extract_value(frame, "heart_rate", int))
            cads.append(_extract_value(frame, "cadence", int))
        elif frame.name == "lap":
            lap_number += 1
        elif frame.name == "session":
            sport = _extract_str(frame, "sport")

    laps = np.array(laps, dtype=np.uint16)
    lats = _convert_fit_coords_to_deg(np.array(lats, dtype=np.float32))
    lons = _convert_fit_coords_to_deg(np.array(lons, dtype=np.float32))
    eles = np.array(eles, dtype=np.float32)
    dists = np.array(dists, dtype=np.float32)
    speeds = np.array(speeds, dtype=np.float32)
    hrs = np.array(hrs, dtype=np.uint8)
    cads = np.array(cads, dtype=np.uint8)

    return sport, pd.DataFrame(
        {
            "lap": laps,
            "timestamp": pd.to_datetime(times),
            "latitude": lats,
            "longitude": lons,
            "distance": dists,
            "speed": speeds,
            "altitude": eles,
            "heart_rate": hrs,
            "cadence": cads,
        }
    )
