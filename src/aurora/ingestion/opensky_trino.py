"""
OpenSky Network Trino Ingestion Client
Implements historical ADS-B queries against trino.opensky-network.org as specified in:
https://openskynetwork.github.io/opensky-api/trino.html
"""

from typing import Iterator, Optional, Dict, Any
import logging
import pandas as pd
from ..utils.memory import enforce_memory_limit

logger = logging.getLogger("aurora.ingestion.opensky_trino")


class OpenSkyTrinoClient:
    """
    Connects to OpenSky Network's historical Trino database (trino.opensky-network.org:443).
    Queries state_vectors_data4 / readsb_mlat_sv with spatial-temporal bounding.
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        catalog: str = "minio",
        schema: str = "osky",
    ):
        self.host = "trino.opensky-network.org"
        self.port = 443
        self.username = username
        self.password = password
        self.catalog = catalog
        self.schema = schema
        self._connection = None

    def connect(self):
        """Establishes SSL connection to OpenSky Trino."""
        try:
            import trino.dbapi
            from trino.auth import BasicAuthentication

            auth = None
            if self.username and self.password:
                auth = BasicAuthentication(self.username, self.password)

            self._connection = trino.dbapi.connect(
                host=self.host,
                port=self.port,
                user=self.username or "anonymous",
                auth=auth,
                http_scheme="https",
                catalog=self.catalog,
                schema=self.schema,
            )
            logger.info("Connected to OpenSky Network Trino database.")
        except ImportError:
            logger.error("trino library is required for OpenSky Trino queries.")
            raise

    @staticmethod
    def build_adiz_query(
        start_epoch: int,
        end_epoch: int,
        bbox: Optional[Dict[str, float]] = None,
        table: str = "state_vectors_data4",
        min_altitude_m: Optional[float] = None,
        max_altitude_m: Optional[float] = None,
    ) -> str:
        """
        Builds optimized OpenSky Trino SQL query for Taiwan ADIZ / GIUK Gap bounding.
        Default bbox: Taiwan Strait area (lat: 20-26, lon: 116-124).
        """
        bbox = bbox or {"min_lat": 20.0, "max_lat": 26.0, "min_lon": 116.0, "max_lon": 124.0}

        clauses = [
            f"time >= {start_epoch}",
            f"time <= {end_epoch}",
            f"lat >= {bbox['min_lat']}",
            f"lat <= {bbox['max_lat']}",
            f"lon >= {bbox['min_lon']}",
            f"lon <= {bbox['max_lon']}",
        ]

        if min_altitude_m is not None:
            clauses.append(f"baroaltitude >= {min_altitude_m}")
        if max_altitude_m is not None:
            clauses.append(f"baroaltitude <= {max_altitude_m}")

        where_str = " AND ".join(clauses)

        return f"""
        SELECT 
            time as timestamp_epoch,
            icao24,
            callsign,
            lat,
            lon,
            baroaltitude * 3.28084 as altitude_ft,
            velocity * 1.94384 as velocity_kts,
            heading as heading_deg,
            onground
        FROM {table}
        WHERE {where_str}
        ORDER BY time ASC
        """

    @enforce_memory_limit(max_mb=512.0)
    def query_stream_chunks(
        self, sql_query: str, chunk_size: int = 50000
    ) -> Iterator[pd.DataFrame]:
        """Streams OpenSky historical telemetry in memory-bounded DataFrame chunks."""
        if self._connection is None:
            self.connect()

        cursor = self._connection.cursor()
        try:
            cursor.execute(sql_query)
            col_names = [col[0] for col in cursor.description]
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                yield pd.DataFrame(rows, columns=col_names)
        finally:
            cursor.close()
