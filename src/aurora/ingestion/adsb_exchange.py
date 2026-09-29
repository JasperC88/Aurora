"""
Live ADS-B Ingestion Client
Pulls live aerial telemetry from ADS-B Exchange (readsb) and OpenSky Network REST endpoints.
References:
- ADS-B Exchange Developer Hub: https://www.adsbexchange.com/community/developer-hub/
- OpenSky REST API: https://openskynetwork.github.io/opensky-api/rest.html
"""

import urllib.request
import json
import logging
from typing import Dict, Any, List, Optional, Union

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    pd = None
    HAS_PANDAS = False

logger = logging.getLogger("aurora.ingestion.adsb_live")


class RecordList(list):
    """Fallback container mimicking basic DataFrame methods when pandas is not installed."""

    def to_dict(self, orient: str = "records") -> List[Dict[str, Any]]:
        return list(self)

    def dropna(self, subset: Optional[List[str]] = None) -> "RecordList":
        if not subset:
            return self
        filtered = [
            row for row in self
            if all(row.get(col) is not None for col in subset)
        ]
        return RecordList(filtered)


class LiveADSBClient:
    """Fetches real-time telemetry from ADS-B Exchange and OpenSky Network."""

    @staticmethod
    def fetch_adsb_exchange_radius(
        lat: float = 23.5,
        lon: float = 119.5,
        dist_nm: int = 250,
        military_only: bool = False,
    ) -> Any:
        """
        Pulls live aircraft around a coordinate center using ADS-B Exchange / readsb v2 API.
        Default center: Taiwan Strait (23.5°N, 119.5°E, 250nm radius).
        """
        endpoint = f"https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist_nm}"
        req = urllib.request.Request(
            endpoint,
            headers={"User-Agent": "Project-Aurora-Researcher/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Error fetching from ADS-B Exchange endpoint: {e}")
            return pd.DataFrame() if HAS_PANDAS else RecordList()

        aircraft_list = data.get("ac", [])
        if not aircraft_list:
            return pd.DataFrame() if HAS_PANDAS else RecordList()

        rows = []
        for ac in aircraft_list:
            is_mil = bool(ac.get("dbFlags", 0) & 1) or ac.get("military", False)
            if military_only and not is_mil:
                continue

            rows.append({
                "hex": ac.get("hex", "").strip().lower(),
                "flight": ac.get("flight", "").strip(),
                "aircraft_type": ac.get("t", "UNK"),
                "registration": ac.get("r", ""),
                "lat": ac.get("lat"),
                "lon": ac.get("lon"),
                "altitude_ft": ac.get("alt_baro", ac.get("alt_geom", 0)),
                "velocity_kts": ac.get("gs", 0.0),
                "track_deg": ac.get("track", 0.0),
                "squawk": ac.get("squawk", ""),
                "is_military": is_mil,
                "timestamp_seen": ac.get("seen_pos", 0),
            })

        if HAS_PANDAS:
            df = pd.DataFrame(rows)
            return df.dropna(subset=["lat", "lon"])
        return RecordList(rows).dropna(subset=["lat", "lon"])

    @staticmethod
    def fetch_opensky_live_bbox(
        min_lat: float = 20.0,
        max_lat: float = 26.0,
        min_lon: float = 116.0,
        max_lon: float = 124.0,
    ) -> Any:
        """
        Pulls live aircraft within a bounding box from OpenSky Network REST API.
        """
        endpoint = (
            f"https://opensky-network.org/api/states/all?"
            f"lamin={min_lat}&lamax={max_lat}&lomin={min_lon}&lomax={max_lon}"
        )
        req = urllib.request.Request(
            endpoint,
            headers={"User-Agent": "Project-Aurora-Researcher/1.0"},
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.error(f"Error fetching from OpenSky Network API: {e}")
            return pd.DataFrame() if HAS_PANDAS else RecordList()

        states = data.get("states", [])
        if not states:
            return pd.DataFrame() if HAS_PANDAS else RecordList()

        rows = []
        for s in states:
            # OpenSky state vector format:
            # 0: icao24, 1: callsign, 2: origin_country, 5: lon, 6: lat, 7: baro_altitude (m), 9: velocity (m/s), 10: heading
            alt_m = s[7]
            alt_ft = alt_m * 3.28084 if alt_m is not None else 0.0
            vel_ms = s[9]
            vel_kts = vel_ms * 1.94384 if vel_ms is not None else 0.0

            rows.append({
                "hex": s[0],
                "flight": (s[1] or "").strip(),
                "country": s[2],
                "lon": s[5],
                "lat": s[6],
                "altitude_ft": round(alt_ft, 1),
                "velocity_kts": round(vel_kts, 1),
                "track_deg": s[10] or 0.0,
                "is_military": False,  # OpenSky basic state does not tag military flags
                "timestamp_seen": s[3] or s[4],
            })

        if HAS_PANDAS:
            df = pd.DataFrame(rows)
            return df.dropna(subset=["lat", "lon"])
        return RecordList(rows).dropna(subset=["lat", "lon"])

