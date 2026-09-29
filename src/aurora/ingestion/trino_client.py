"""
Trino Ingestion Client for Project Aurora
Handles chunked, streaming ingestion from Trino clusters (or Presto) to avoid high memory spikes.
"""

from typing import Iterator, Dict, Any, Optional, List
import pandas as pd
import logging

logger = logging.getLogger("aurora.ingestion.trino")


class TrinoIngestionClient:
    """
    Connects to a Trino telemetry data lake and yields query results
    in strictly memory-bounded DataFrame chunks.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8080,
        user: str = "aurora_researcher",
        catalog: str = "hive",
        schema: str = "telemetry",
        http_scheme: str = "http",
    ):
        self.connection_params = {
            "host": host,
            "port": port,
            "user": user,
            "catalog": catalog,
            "schema": schema,
            "http_scheme": http_scheme,
        }
        self._connection = None

    def connect(self):
        """Lazy connection to Trino database."""
        try:
            import trino.dbapi

            self._connection = trino.dbapi.connect(**self.connection_params)
            logger.info(f"Connected to Trino at {self.connection_params['host']}:{self.connection_params['port']}")
        except ImportError:
            logger.warning("Trino client library not installed. Mock or local testing mode enabled.")
            self._connection = None

    def stream_query_chunks(
        self, query: str, chunk_size: int = 50000
    ) -> Iterator[pd.DataFrame]:
        """
        Executes a SQL query on Trino and streams results in chunks of size `chunk_size`
        to prevent holding large telemetry results in memory.
        """
        if self._connection is None:
            self.connect()

        if self._connection is None:
            raise RuntimeError(
                "Cannot stream from Trino: 'trino' package is not installed or connection failed."
            )

        cursor = self._connection.cursor()
        try:
            cursor.execute(query)
            col_names = [desc[0] for desc in cursor.description]
            while True:
                rows = cursor.fetchmany(chunk_size)
                if not rows:
                    break
                yield pd.DataFrame(rows, columns=col_names)
        finally:
            cursor.close()

    @staticmethod
    def build_bounding_query(
        table: str,
        start_time: str,
        end_time: str,
        bbox: Optional[Dict[str, float]] = None,
        altitude_col: str = "altitude_ft",
        min_altitude: Optional[float] = None,
        max_altitude: Optional[float] = None,
    ) -> str:
        """
        Build an efficient, push-down SQL query filtering on timestamp and bounding envelope.
        Bbox format: {'min_lon': float, 'max_lon': float, 'min_lat': float, 'max_lat': float}
        """
        conditions = [
            f"timestamp >= TIMESTAMP '{start_time}'",
            f"timestamp <= TIMESTAMP '{end_time}'",
        ]

        if bbox:
            conditions.append(f"lon >= {bbox['min_lon']} AND lon <= {bbox['max_lon']}")
            conditions.append(f"lat >= {bbox['min_lat']} AND lat <= {bbox['max_lat']}")

        if min_altitude is not None:
            conditions.append(f"{altitude_col} >= {min_altitude}")
        if max_altitude is not None:
            conditions.append(f"{altitude_col} <= {max_altitude}")

        where_clause = " AND ".join(conditions)
        return f"SELECT * FROM {table} WHERE {where_clause} ORDER BY timestamp ASC"
