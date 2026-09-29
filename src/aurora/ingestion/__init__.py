"""Project Aurora: Telemetry Ingestion Layer."""

try:
    from .trino_client import TrinoIngestionClient
except ImportError:
    TrinoIngestionClient = None

try:
    from .dask_loader import load_partitioned_telemetry
except ImportError:
    load_partitioned_telemetry = None

try:
    from .opensky_trino import OpenSkyTrinoClient
except ImportError:
    OpenSkyTrinoClient = None

try:
    from .adsb_exchange import LiveADSBClient
except ImportError:
    LiveADSBClient = None

__all__ = [
    "TrinoIngestionClient",
    "load_partitioned_telemetry",
    "OpenSkyTrinoClient",
    "LiveADSBClient",
]
