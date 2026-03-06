# ISPU Data Integration Service

> **Environmental Data Aggregation & Persistence Service**
>
> Automated background worker service that collects air quality and weather monitoring data from ISPU APIs and persists to MySQL database on a scheduled basis.

---

## Project Overview

### Project Classification
**Data Integration Service** - Containerized ETL-like application for continuous environmental monitoring data aggregation.

### Target Audience
- **Infrastructure & DevOps Engineers** - Container deployment and management
- **Data Engineers** - Building data pipelines and integration workflows
- **Environmental Organizations** - Air quality and weather data collection infrastructure
- **System Administrators** - Background service operations and monitoring

### Primary Purpose
Automatically retrieves environmental data (air quality indices, pollutants, weather parameters) from multiple ISPU API endpoints at regular intervals, transforms/validates the data, and stores it in a MySQL database for subsequent analysis, reporting, and alerting systems.

---

## Architecture & Program Flow

### High-Level Flow

```
┌───────────────────────────────────────────────────┐
│ Application Start (via Supervisor)                │
└─────────────────────┬─────────────────────────────┘
                      │
        ┌─────────────▼──────────────┐
        │ Infinite Scheduler Loop    │
        │ Execution: Every 60s @ :04 │
        └──────────────┬─────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
   ┌───▼───┐      ┌────▼────┐    ┌────▼────┐
   │ ISPU  │      │ Latest  │    │ Weather │
   │Latest │      │  Data   │    │Data     │
   └───┬───┘      └────┬────┘    └────┬────┘
       │               │              │
       └───────────────┼──────────────┘
                       │
            ┌──────────▼──────────┐
            │ Parse JSON Rows     │
            │ Map Parameters      │
            │ Check Duplicates    │
            │ Insert to MySQL     │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │ Log Results & Stats │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │ Rotate Logs if >6000│
            │ lines               │
            └──────────┬──────────┘
                       │
         Sleep til next cycle (60s)
```

### Execution Details

**Frequency**: Every minute at second 4 (00:04, 01:04, 02:04, etc.)

**Sequential Task Execution**:
1. **ISPU Latest** - Air Quality Index data
2. **Latest Weather** - Weather and meteorological data  
3. **Latest Data** - Supplementary pollutant parameters

Each task operates independently:
- Fetches from dedicated API endpoint
- Parses received JSON
- Transforms & validates data
- Persists to database
- Logs operation results

**Operation Continuity**:
- Supervisor automatically restarts on failure
- Service continues on API/database errors (logged)
- Graceful shutdown on `CTRL+C`
- Log file auto-rotation to prevent disk bloat

---

## Directory Structure

```
apiIspu/
│
├── backend/                              # Core Python application modules
│   ├── main.py                          # Scheduler orchestration & entry point
│   ├── config.py                        # Database connectivity & insert operations
│   ├── dataIspuLatest.py               # ISPU air quality index data handler
│   ├── dataLatest.py                   # Supplementary air quality handler
│   └── dataLatestWeather.py            # Weather/meteorological data handler
│
├── logs/                                # Runtime execution logs (auto-managed)
│   ├── main.log                        # Application operation logs
│   └── supervisord.log                 # Process supervisor logs
│
├── Dockerfile                           # Container image specification
├── docker-compose.yml                  # Docker Compose orchestration config
├── supervisord.conf                    # Supervisor process management config
├── requirements.txt                    # Python package dependencies
├── deploy.sh                           # Automated deployment script
├── .env                                # Environment configuration (local)
├── .env.example                        # Configuration template (for VCS)
├── .gitignore                          # Git exclude patterns
└── README.md                           # This file
```

### Component Descriptions

| Component | Purpose | Type |
|-----------|---------|------|
| **backend/** | Core application logic and data handlers | Python modules |
| **logs/** | Timestamped execution records and debug information | Log files |
| **Dockerfile** | Container image with Python 3.11 runtime and supervisor | Infrastructure |
| **docker-compose.yml** | Service orchestration and configuration | Infrastructure |
| **supervisord.conf** | Background process lifecycle management | Configuration |
| **requirements.txt** | External Python package specifications | Dependencies |
| **.env / .env.example** | Application configuration and credentials | Configuration |

---

## Getting Started

### Prerequisites

- **Docker & Docker Compose** installed and running
- **MySQL Server** (version 5.7+) accessible and configured
- **Target Database** created with required table schema

### Database Setup

Execute the following SQL to create the target table:

```sql
CREATE TABLE IF NOT EXISTS tbl_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    recorded_at VARCHAR(255) NOT NULL,
    timestamp INT NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    parameter_name VARCHAR(255) NOT NULL,
    value VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY unique_data (recorded_at, device_id, parameter_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

**Index Note**: The `UNIQUE KEY` composite index prevents duplicate records on same device/parameter/datetime combination.

### Configuration Setup

The service requires environment configuration. A template is provided:

```bash
# Copy template to local configuration
cp .env.example .env

# Edit with actual values (API credentials, database connection parameters, etc.)
# Refer to .env.example for all available configuration options
nano .env
```

**Configuration Note**: `.env` file is excluded from version control. Each deployment instance requires its own `.env` configuration.

### Deployment

#### Option 1: Automated Deployment (Recommended)

```bash
# Execute deployment script (builds and starts container)
./deploy.sh

# View real-time logs
docker-compose logs -f ispu
```

#### Option 2: Manual Docker Compose

```bash
# Build container image
docker-compose build

# Start service in background
docker-compose up -d

# Monitor logs
docker-compose logs -f ispu

# Stop service
docker-compose stop ispu

# View service status
docker-compose ps
```

#### Option 3: Direct Python Execution (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Execute main scheduler
cd backend
python main.py
```

---

## Data Integration

### API Data Sources

The service aggregates data from three independent API endpoints:

#### 1. ISPU Latest (Air Quality Index)
**Function**: `ispuLatest()`  
**Data Type**: Air Quality Index values for pollutants  
**Processing**: Extracted field `ispu` from parameters  
**Mapped Parameters**:
- PM10 → `ipm10`
- PM2.5 → `ipm25`
- O3 → `io3`
- SO2 → `iso2`
- NO2 → `ino2`
- CO → `ico`
- HC → `ihc`

#### 2. Latest Weather (Meteorological Data)
**Function**: `latestWeather()`  
**Data Type**: Weather and atmospheric measurements  
**Processing**: Extracted field `val` from parameters  
**Mapped Parameters**:
- Temperature → `atemp`
- Humidity → `hum`
- Pressure → `apress`
- Wind Speed → `wspeed`
- Wind Direction → `wdir`
- Rainfall → `rain`
- Solar Radiation → `srad`

#### 3. Latest Data (Supplementary Pollutants)
**Function**: `latest()`  
**Data Type**: Pollutant concentration levels  
**Processing**: Extracted field `val` from parameters  
**Mapped Parameters**:
- PM10 → `pm10`
- PM2.5 → `pm25`
- O3 → `o3`
- SO2 → `so2`
- NO2 → `no2`
- CO → `co`
- HC → `hc`

### Data Flow & Transformation

**Input Format** (from API):
```json
{
  "rows": [
    {
      "deviceId": "DEVICE001",
      "values": [
        {
          "datetime": "2026-03-06 12:00:00",
          "parameters": [
            {
              "label": "Temperature",
              "val": "28.5"
            }
          ]
        }
      ]
    }
  ]
}
```

**Processing Steps**:
1. Parse JSON response
2. Iterate devices (rows)
3. For each dated entry (values), iterate parameters
4. Extract `label` and appropriate value field (`val` or `ispu`)
5. Map parameter label to database field name
6. Convert datetime string to Unix timestamp
7. Check for existing record (duplicate prevention)
8. Insert into `tbl_data` if not duplicate

**Output Format** (persisted to database):
```
recorded_at: 2026-03-06 12:00:00
timestamp: 1741248000
device_id: DEVICE001
parameter_name: atemp
value: 28.5
created_at: 2026-03-06 12:05:30.123
updated_at: 2026-03-06 12:05:30.123
```

### Data Validation & Filtering

**Records are inserted only when**:
- Device ID is present in source data
- Datetime is present and parseable (ISO format: `YYYY-MM-DD HH:MM:SS`)
- Parameter label exists in configured mapping
- Value field is non-null
- No duplicate record exists (composite key: recorded_at + device_id + parameter_name)

**Records are skipped when**:
- Any required field is missing/invalid
- Parameter label not in mapping (filtered intentionally)
- Duplicate entry detected
- Error during datetime parsing or database insertion

---

## Logging & Operations

### Log Files

| Log | Location | Purpose |
|-----|----------|---------|
| Application | `/app/logs/main.log` | Service execution, data insertion, errors |
| Supervisor | `/app/logs/supervisord.log` | Process manager events |

### Log Rotation

**Automatic Log Cleanup**:
- **Trigger**: At each execution cycle (every minute)
- **Condition**: Activates when log exceeds 6,000 lines
- **Action**: Retains most recent 6,000 lines, discards older entries
- **Purpose**: Prevents unbounded disk usage in long-running deployments

### Log Entry Examples

```
[2026-03-06 12:05:04] Menjalankan task pengambilan data dari API Ispu Latest...
[2026-03-06 12:05:05] Data berhasil disimpan kedatabase: device='DEVICE001', datetime='2026-03-06 12:00:00', parameter='atemp', value='28.5'
[2026-03-06 12:05:05] Parsing selesai. Success: 7, Skipped: 2, Failed: 0
[2026-03-06 12:05:06] Menjalankan task pengambilan data dari API Latest Weather...
```

---

## Troubleshooting

### Common Issues & Solutions

#### Service Not Starting
**Symptoms**: Container exits immediately or supervisor fails to start  
**Checks**:
- Verify `.env` file exists and has correct values
- Check database connectivity: `telnet <DB_HOST> <DB_PORT>`
- Review logs: `docker-compose logs ispu`
- Ensure Python dependencies installed: `pip install -r requirements.txt`

#### No Data Being Inserted
**Symptoms**: Service runs but database remains empty  
**Causes & Solutions**:
- Verify database table exists with correct schema (see Database Setup section)
- Check API responses (may contain error status instead of data)
- Review application logs for parsing errors
- Confirm parameter mappings match received parameter labels

#### High CPU Usage
**Symptoms**: Container consuming excessive CPU  
**Likely Causes**:
- Scheduler cycle duration shorter than API response time
- Inefficient database queries
- Excessive logging volume
- API returning large datasets

#### Database Connection Errors
**Symptoms**: "Connection refused" or "Access denied" errors in logs  
**Checks**:
- MySQL server running: `systemctl status mysql`
- Network connectivity to DB host
- Credentials in `.env` match MySQL user permissions
- MySQL port accessible from container (Docker network)

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `mysql-connector-python` | 8.1.0 | MySQL database connection |
| `requests` | 2.32.0 | HTTP API requests |
| `PyJWT` | 2.8.0 | JWT handling (present but not actively used) |
| `python-dotenv` | 1.0.0 | Environment variable management |

---

## Docker Operations

### Image Management

```bash
# Build without cache (fresh dependencies)
docker-compose build --no-cache ispu

# Build with cache (faster)
docker-compose build ispu
```

### Container Lifecycle

```bash
# Start service
docker-compose up -d ispu

# Stop service
docker-compose stop ispu

# Restart service
docker-compose restart ispu

# Remove container (data in database persists)
docker-compose down

# View running status
docker-compose ps
```

### Monitoring

```bash
# Real-time logs (follow mode)
docker-compose logs -f ispu

# Last 100 lines
docker-compose logs --tail=100 ispu

# Container resource usage
docker stats api_ispu
```

### Container Configuration

| Setting | Value | Details |
|---------|-------|---------|
| **Base Image** | python:3.11-slim | Lightweight Python runtime |
| **Working Directory** | /app | Application root in container |
| **Network Mode** | Host | Direct network access (for localhost databases) |
| **Restart Policy** | Always | Auto-restart on failure |
| **Process Manager** | Supervisor | Background process lifecycle management |

---

## Configuration Reference

### Environment Variables

All configuration is externalized via environment variables (loaded from `.env` file):

**API Configuration**:
- `APIENDPOINT_ISPU_LATEST` - ISPU air quality index endpoint
- `APIENDPOINT_LATEST_WEATHER` - Weather data endpoint
- `APIENDPOINT_LATEST` - Supplementary parameters endpoint
- `ISPU_APIKEY` - API authentication key
- `ISPU_APISECRET` - API authentication secret

**Database Configuration**:
- `MYSQL_HOST` - Database server hostname/IP
- `MYSQL_USER` - Database user account
- `MYSQL_PASSWORD` - User password
- `MYSQL_DATABASE` - Target database name
- `MYSQL_PORT` - MySQL server port

**Application Configuration**:
- `LOG_MAX_LINES` - Log retention size (lines before rotation)
- `LOG_FILE_PATH` - Absolute path to application log file

See `.env.example` for template with all available options.

---

## Scheduler Behavior

### Timing & Precision

- **Execution Interval**: 60 seconds (one minute)
- **Execution Time**: At second `:04` of each minute (00:04, 01:04, etc.)
- **Precision**: Approximate (±few milliseconds)
- **Consistency**: Maintains scheduler loop despite API delays

### Failover Behavior

| Scenario | Behavior |
|----------|----------|
| API Connection Failure | Error logged; retry at next cycle |
| Database Error | Error logged; retry at next cycle |
| Timeout | Request aborted; retry at next cycle |
| Malformed Data | Entries skipped; valid entries inserted |
| Exception During Task | Error logged; loop continues to next task |
| Container Crash | Supervisor auto-restarts service |

---

## Performance Characteristics

### Execution Profile

- **Typical Cycle Duration**: 10-30 seconds (variable based on API response times)
- **Memory Footprint**: ~80-150MB (Python process)
- **Database Connections**: New connection per database operation (closed after use)
- **API Request Timeout**: 5-60 seconds (varies by endpoint)

### Scaling Considerations

**Current Limitations**:
- Single-threaded execution (sequential API calls)
- Database connection per operation (no pooling)
- Parameter mappings hardcoded in source
- Single device source (no multi-location aggregation)

**Note**: For high-volume requirements, consider implementing connection pooling, parallel API calls, or distributed processing architecture.

---

## Code Organization

### Module Responsibilities

| Module | Responsibility |
|--------|-----------------|
| `main.py` | Scheduler loop orchestration, log rotation |
| `config.py` | Database connectivity, data insertion, duplicate checking |
| `dataIspuLatest.py` | ISPU API integration, air quality data parsing |
| `dataLatest.py` | Supplementary data API integration, parameter mapping |
| `dataLatestWeather.py` | Weather API integration, meteorological data parsing |

### Shared Patterns

- **Logging**: All modules use `write_log()` function for timestamped output
- **API Handling**: Consistent error handling and timeout management
- **Data Parsing**: Structured JSON iteration with validation
- **Parameter Mapping**: Label-based field name transformation
- **Database Operations**: Uniform INSERT with duplicate prevention

---

## Important Notes

### Operational Constraints

1. **Single Deployment**: Service designed for single-instance execution. Multiple instances may cause duplicate insertions or concurrent database issues.

2. **Datetime Accuracy**: Timestamps reflect API data time, not system time. Ensure device clock synchronization for meaningful temporal analysis.

3. **Data Completeness**: Missing API responses result in no data for that cycle. Not retroactively fetched; gaps appear in historical data.

4. **Parameter Filtering**: Only explicitly mapped parameters are persisted. Unmapped parameters are silently discarded.

### Future Enhancement Opportunities

*(Not currently implemented)*
- Configuration-driven parameter mappings (without code changes)
- Multi-location support (aggregating multiple device installations)
- Bulk insert optimization (batch processing)
- Data quality metrics and anomaly detection
- Monitoring endpoints (health check, metrics export)
- Configurable scheduler intervals
- API retry logic with exponential backoff

---

## License & Attribution

- **Service**: ISPU Data Integration Service
- **Data Source**: ISPU (Indeks Standar Pencemar Udara) 
- **Runtime**: Docker + Python 3.11
- **Last Updated**: March 2026

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Maintenance**: Active
