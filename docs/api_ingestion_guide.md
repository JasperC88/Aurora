# Project Aurora: API Telemetry Ingestion Guide

This guide details how to ingest live and historical spatial telemetry from **ADS-B Exchange** and the **OpenSky Network** into Project Aurora's memory-disciplined pipeline.

---

## Architecture & Memory Discipline
All ingestion clients adhere to Project Aurora's core architectural rule:
- **Never load raw telemetry datasets entirely into memory.**
- Continuous streams and queries are partitioned into discrete chunks ($\le 50,000$ rows) and guarded by [`MemoryGuard`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/utils/memory.py) to remain strictly $\le 512\text{ MB RAM}$.

---

## 1. Method 1: Live ADS-B Exchange / readsb REST API
**Best for:** Real-time operational monitoring, identifying military aircraft, and calculating immediate boundary dwell times.

### Endpoints
* **Radial Geographic Query:**  
  `https://api.adsb.lol/v2/lat/{lat}/lon/{lon}/dist/{dist_nm}`
* **Global Military Filter:**  
  `https://api.adsb.lol/v2/mil`

### Python Ingestion Example
Use [`LiveADSBClient`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/ingestion/adsb_exchange.py):

```python
from aurora.ingestion.adsb_exchange import LiveADSBClient

# Pull all live aircraft within 250 NM of Taiwan Strait center (23.5°N, 119.5°E)
records = LiveADSBClient.fetch_adsb_exchange_radius(
    lat=23.5, 
    lon=119.5, 
    dist_nm=250, 
    military_only=False  # Set True to filter exclusively for military airframes
)

print(f"Tracked {len(records)} aircraft.")
for ac in records[:3]:
    print(f"Callsign: {ac['flight']}, Alt: {ac['altitude_ft']} ft, Hdg: {ac['track_deg']}°")
```

### CLI One-Liner (cURL)
```bash
curl -s "https://api.adsb.lol/v2/lat/23.5/lon/119.5/dist/250" | jq '.ac[0]'
```

---

## 2. Method 2: OpenSky Network Live REST API
**Best for:** Broad regional baselining and cross-validating commercial flight corridors against military incursion paths.

### Endpoint
* **Bounding Box Query:**  
  `https://opensky-network.org/api/states/all?lamin={min_lat}&lamax={max_lat}&lomin={min_lon}&lomax={max_lon}`

### Rate Limits
* **Anonymous Requests:** Max 1 query per 10 seconds.
* **Registered Accounts:** Max 1 query per 5 seconds.

### Python Ingestion Example
```python
from aurora.ingestion.adsb_exchange import LiveADSBClient

# Pull state vectors bounded to Taiwan ADIZ airspace (20°N to 26°N, 116°E to 124°E)
states = LiveADSBClient.fetch_opensky_live_bbox(
    min_lat=20.0,
    max_lat=26.0,
    min_lon=116.0,
    max_lon=124.0
)

print(f"Received {len(states)} active aircraft state vectors.")
```

### CLI One-Liner (cURL)
```bash
curl -s "https://opensky-network.org/api/states/all?lamin=20.0&lamax=26.0&lomin=116.0&lomax=124.0" | jq '.states[0]'
```

---

## 3. Method 3: OpenSky Network Historical Trino SQL API
**Best for:** Empirical dissertation analysis across months of historical PLA incursions or GIUK Gap transits.

### Connection Specifications
* **Host:** `trino.opensky-network.org:443`
* **Protocol:** HTTPS / SSL with Basic Authentication (requires free OpenSky researcher credentials).
* **Database Catalog & Schema:** `minio.osky`
* **Primary Tables:**
  * `state_vectors_data4`: 1-second interpolated state vectors.
  * `readsb_mlat_sv`: Multilateration surveillance data.

### Python Ingestion Example
Use [`OpenSkyTrinoClient`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/ingestion/opensky_trino.py):

```python
from aurora.ingestion.opensky_trino import OpenSkyTrinoClient

# 1. Initialize client with OpenSky researcher credentials
client = OpenSkyTrinoClient(username="your_opensky_user", password="your_password")

# 2. Build pushdown bounding query for Taiwan ADIZ across a 24-hour epoch range
query = OpenSkyTrinoClient.build_adiz_query(
    start_epoch=1704067200,  # 2024-01-01 00:00:00 UTC
    end_epoch=1704153600,    # 2024-01-02 00:00:00 UTC
    bbox={"min_lat": 20.0, "max_lat": 26.0, "min_lon": 116.0, "max_lon": 124.0}
)

# 3. Stream query results in memory-safe chunks (50,000 rows each)
for chunk_df in client.query_stream_chunks(query, chunk_size=50000):
    print(f"Processing chunk with {len(chunk_df)} rows...")
    # Feed chunk_df directly into SpatialJoinEngine
```

---

## 4. Method 4: Automated Continuous Collector Daemon
Project Aurora includes an automated collector daemon ([`src/aurora/ingestion/collector.py`](file:///Users/jasper/Documents/Project%20Aurora/src/aurora/ingestion/collector.py)) that polls live APIs at regular intervals, guards memory, and appends to hourly partitioned files in `data/raw/`.

### Running the Collector
```bash
# Ingest live ADS-B Exchange data in Taiwan theater every 15 seconds
python3 -m aurora.ingestion.collector --source adsb --theater taiwan --interval 15 --out-dir data/raw

# Filter exclusively for military airframes in Taiwan theater
python3 -m aurora.ingestion.collector --source adsb --theater taiwan --mil-only --interval 10

# Ingest live OpenSky data in GIUK Gap theater every 30 seconds
python3 -m aurora.ingestion.collector --source opensky --theater giuk --interval 30 --out-dir data/raw
```

Partitioned files are written directly as:
`data/raw/telemetry_<theater>_<source>_<YYYYMMDD>_<HH>.csv`
ready for downstream processing via `batch_runner.py`.
