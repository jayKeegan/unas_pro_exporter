# UNAS Pro Exporter

A Prometheus exporter for UNAS Pro NAS devices that collects and exposes hardware and storage metrics for monitoring and alerting.

## Features

- **System Metrics**: CPU usage, temperature, memory utilization
- **Storage Metrics**: Drive health, temperatures, storage usage, quotas
- **Share Metrics**: Personal and shared drive usage and quotas
- **Network Metrics**: Network interface status
- **Firmware Monitoring**: Track firmware version and update availability
- **Docker Ready**: Fully containerized with Docker and Docker Compose support

## Metrics Exported

| Metric Name | Description | Labels | Type |
|-------------|-------------|--------|------|
| `device_name` | Device name | `name` | Gauge |
| `cpu_usage` | CPU usage percentage | - | Gauge |
| `cpu_temperature` | CPU temperature in Celsius | - | Gauge |
| `memory_free` | Free memory in MB | - | Gauge |
| `memory_used` | Used memory in MB | - | Gauge |
| `memory_total` | Total memory in MB | - | Gauge |
| `memory_usage` | Memory usage percentage | - | Gauge |
| `firmware` | Firmware status (1=latest, 0=outdated) | `version` | Gauge |
| `drive_temperature` | Drive temperature in Celsius | `slot` | Gauge |
| `drive_healthy` | Drive health status (1=healthy, 0=unhealthy) | `slot` | Gauge |
| `drive_size` | Drive size in bytes | `slot` | Gauge |
| `total_storage` | Total storage in bytes | - | Gauge |
| `used_storage` | Used storage in bytes | - | Gauge |
| `free_storage` | Free storage in bytes | - | Gauge |
| `share` | Share size in bytes | `name`, `quota` | Gauge |
| `start_time` | Device start time (Unix timestamp) | - | Gauge |
| `network_interface` | Network interface status (1=connected, 0=disconnected) | `interface` | Gauge |

## Prerequisites

- UNAS Pro device with API access
- Python 3.13+ (for local development)
- Docker and Docker Compose (for containerized deployment)
- Prometheus server (for metrics collection)

## Installation

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/jaykeegan/unas_pro_exporter.git
cd unas_pro_exporter
```

2. Edit the `docker-compose.yml` file and configure environment variables:
```yaml
environment:
  - DEBUG=false
  - PORT=9101
  - DEVICE_HOSTNAME=your-unas-device.local
  - DEVICE_USERNAME=your-username
  - DEVICE_PASSWORD=your-password
  - CHECK_FREQUENCY=5
```

3. Start the exporter:
```bash
docker-compose up -d
```

4. Verify the exporter is running:
```bash
curl http://localhost:9101/metrics
```

### Option 2: Docker

```bash
docker run -d \
  --name unas-pro-exporter \
  -p 9101:9101 \
  -e DEVICE_HOSTNAME=your-unas-device.local \
  -e DEVICE_USERNAME=your-username \
  -e DEVICE_PASSWORD=your-password \
  -e CHECK_FREQUENCY=5 \
  ghcr.io/jaykeegan/unas_pro_exporter:latest
```

### Option 3: Local Python

1. Clone the repository:
```bash
git clone https://github.com/jaykeegan/unas_pro_exporter.git
cd unas_pro_exporter
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file:
```bash
PORT=9101
DEVICE_HOSTNAME=your-unas-device.local
DEVICE_USERNAME=your-username
DEVICE_PASSWORD=your-password
CHECK_FREQUENCY=5
DEBUG=false
```

5. Run the exporter:
```bash
python src/main.py
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PORT` | No | `8000` | Port for the metrics HTTP server |
| `DEVICE_HOSTNAME` | Yes | - | Hostname or IP address of your UNAS Pro device |
| `DEVICE_USERNAME` | Yes | - | Username for UNAS Pro API authentication |
| `DEVICE_PASSWORD` | Yes | - | Password for UNAS Pro API authentication |
| `CHECK_FREQUENCY` | No | `5` | Metrics collection interval in seconds |
| `DEBUG` | No | `false` | Enable debug logging (true/false) |
| `LOGIN_RETRY_FREQUENCY` | No | `10` | Retry interval for failed login attempts in seconds |
| `REQUEST_TIMEOUT` | No | `10` | HTTP request timeout in seconds |

### Security Considerations

- The exporter communicates with UNAS Pro over HTTPS but disables SSL verification
- Store credentials securely (use Docker secrets or environment variable management)
- Consider running the exporter in a trusted network
- Use a dedicated read-only user account if possible

## Usage

### Accessing Metrics

Once running, metrics are available at:
```
http://localhost:9101/metrics
```

### Example Metrics Output

```
# HELP cpu_usage CPU Usage (%)
# TYPE cpu_usage gauge
cpu_usage 23.5

# HELP cpu_temperature CPU Temperature (°C)
# TYPE cpu_temperature gauge
cpu_temperature 45.2

# HELP memory_usage Memory Usage (%)
# TYPE memory_usage gauge
memory_usage 67.8

# HELP drive_temperature Drive Temperature (°C)
# TYPE drive_temperature gauge
drive_temperature{slot="1"} 38.0
drive_temperature{slot="2"} 39.5

# HELP drive_healthy Drive Healthy
# TYPE drive_healthy gauge
drive_healthy{slot="1"} 1.0
drive_healthy{slot="2"} 1.0
```

### Quick Start

Add to your `prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'unas-pro'
    static_configs:
      - targets: ['localhost:9101']
```

For a complete monitoring stack with Prometheus, Grafana, and Alertmanager, see the [Full Stack Example](examples/docker-compose-full-stack.yml).

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to UNAS device
```
Error: Failed to login... trying again in 10 seconds
```

**Solutions**:
- Verify `DEVICE_HOSTNAME` is correct and reachable
- Check username and password are correct
- Ensure the UNAS Pro API is accessible from the exporter's network

### Authentication Failures

**Problem**: Continuous login failures
```
Not logged in... trying again
```

**Solutions**:
- Verify credentials are correct
- Check if the user account is active and not locked
- Ensure the account has API access permissions

### No Metrics Appearing

**Problem**: Metrics endpoint returns empty or incomplete data

**Solutions**:
- Check logs with `docker logs <container-name>`
- Enable debug mode by setting `DEBUG=true`
- Verify the exporter can reach the metrics endpoint: `curl http://localhost:9101/metrics`
- Increase `LOGIN_RETRY_FREQUENCY` if connection is unstable

### High CPU Usage

**Problem**: Exporter consuming too many resources

**Solutions**:
- Increase `CHECK_FREQUENCY` to reduce polling frequency
- Check if debug logging is enabled (disable it in production)

## Development

### Building from Source

```bash
# Build Docker image
docker build -t unas-pro-exporter -f docker/Dockerfile .

# Run locally for testing
python src/main.py
```

### Project Structure

```
.
├── docker/
│   └── Dockerfile                  # Docker container definition
├── src/
│   ├── main.py                    # Main exporter application
│   ├── unas.py                    # UNAS Pro API client
│   └── utils.py                   # Utility functions
├── examples/                       # Example configurations
│   ├── prometheus.yml             # Example Prometheus config
│   ├── unas_alerts.yml            # Alerting rules
│   ├── unas_recording_rules.yml   # Recording rules
│   ├── alertmanager.yml           # Alertmanager config
│   ├── docker-compose-full-stack.yml  # Complete monitoring stack
│   └── grafana/                   # Grafana provisioning
│       └── provisioning/
│           ├── datasources/       # Datasource configs
│           └── dashboards/        # Dashboard configs
├── docker-compose.yml             # Docker Compose configuration
├── requirements.txt               # Python dependencies
├── README.md                      # This file (start here!)
├── QUICKSTART.md                  # 5-minute setup guide
├── PROMETHEUS.md                  # Prometheus integration guide
├── QUERIES.md                     # PromQL query examples
└── CONFIGURATION.md               # Configuration reference
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is open source and available under the MIT License.

## Support

For issues, questions, or contributions, please use the GitHub issue tracker.

## Acknowledgments

- Built with [prometheus_client](https://github.com/prometheus/client_python)
- Designed for UNAS Pro NAS devices
