import numpy as np
import pandas as pd
from lxml import etree
from typing import Union, Type


def _extract_value(
    etree_element: etree.Element, datatype: Union[Type[int], Type[float]]
) -> Union[int, float]:
    if etree_element is None:
        return 0 if datatype is int else np.nan
    return datatype(etree_element.text)


def _get_tcx_cadence(trkpt_ext: etree.Element, ns: dict) -> int:
    run_cadence = trkpt_ext.find("tcxtpx:RunCadence", ns)
    if run_cadence is not None:
        return int(run_cadence.text)
    cadence = trkpt_ext.find("tcxtpx:Cadence", ns)
    if cadence is not None:
        return int(cadence.text)
    return 0


def get_sport_from_gpx(open_file):
    for line in open_file:
        if "<type>" in line:
            start = line.find("<type>") + len("<type>")
            end = line.find("</type>")
            return line[start:end].strip().lower()
    return None


def get_sport_from_tcx(open_file):
    for line in open_file:
        if "<Activity" in line:
            start = line.find('Sport="') + len('Sport="')
            end = line.find('"', start)
            return line[start:end].strip().lower()
    return None


def extract_gpx(gpx_file: str) -> pd.DataFrame:
    ns = {
        "gpx": "http://www.topografix.com/GPX/1/1",
        "gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1",
    }

    times = []
    lats = []
    lons = []
    eles = []
    hrs = []
    cads = []

    for event, trkpt in etree.iterparse(
        gpx_file, events=("end",), tag="{http://www.topografix.com/GPX/1/1}trkpt"
    ):

        times.append(trkpt.find("gpx:time", ns).text)
        lats.append(float(trkpt.attrib["lat"]))
        lons.append(float(trkpt.attrib["lon"]))
        eles.append(_extract_value(trkpt.find("gpx:ele", ns), float))
        extensions = trkpt.find("gpx:extensions", ns)
        if extensions is not None:
            hrs.append(
                _extract_value(
                    extensions.find("gpxtpx:TrackPointExtension/gpxtpx:hr", ns), int
                )
            )
            cads.append(
                _extract_value(
                    extensions.find("gpxtpx:TrackPointExtension/gpxtpx:cad", ns), int
                )
            )

    lats = np.array(lats, dtype=np.float32)
    lons = np.array(lons, dtype=np.float32)
    eles = np.array(eles, dtype=np.float32)
    hrs = np.array(hrs, dtype=np.uint8)
    cads = np.array(cads, dtype=np.uint8)

    return pd.DataFrame(
        {
            "timestamp": pd.to_datetime(times),
            "latitude": lats,
            "longitude": lons,
            "altitude": eles,
            "heart_rate": hrs,
            "cadence": cads,
        }
    )


def extract_tcx(tcx_file: str) -> pd.DataFrame:
    ns = {
        "tcx": "http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2",
        "tcxtpx": "http://www.garmin.com/xmlschemas/ActivityExtension/v2",
    }

    lap_number = 0
    laps = []
    times = []
    lats = []
    lons = []
    eles = []
    dists = []
    speeds = []
    hrs = []
    cads = []

    for event, lap in etree.iterparse(
        tcx_file,
        events=("end",),
        tag="{http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2}Lap",
    ):
        lap_number += 1
        for trkpt in lap.findall(".//tcx:Trackpoint", ns):
            laps.append(lap_number)
            times.append(trkpt.find("tcx:Time", ns).text)
            lats.append(
                _extract_value(
                    trkpt.find("tcx:Position/tcx:LatitudeDegrees", ns), float
                )
            )
            lons.append(
                _extract_value(
                    trkpt.find("tcx:Position/tcx:LongitudeDegrees", ns), float
                )
            )
            eles.append(_extract_value(trkpt.find("tcx:AltitudeMeters", ns), float))
            dists.append(_extract_value(trkpt.find("tcx:DistanceMeters", ns), float))
            hrs.append(
                _extract_value(trkpt.find("tcx:HeartRateBpm/tcx:Value", ns), int)
            )

            extensions = trkpt.find("tcx:Extensions", ns)
            if extensions is not None:
                tpx = extensions.find("tcxtpx:TPX", ns)
                if tpx is not None:
                    speeds.append(_extract_value(tpx.find("tcxtpx:Speed", ns), float))
                    cads.append(_get_tcx_cadence(tpx, ns))

    laps = np.array(laps, dtype=np.uint16)
    lats = np.array(lats, dtype=np.float32)
    lons = np.array(lons, dtype=np.float32)
    eles = np.array(eles, dtype=np.float32)
    dists = np.array(dists, dtype=np.float32)
    speeds = np.array(speeds, dtype=np.float32)
    hrs = np.array(hrs, dtype=np.uint8)
    cads = np.array(cads, dtype=np.uint8)

    return pd.DataFrame(
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
