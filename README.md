# Store Monitoring System

This application monitors restaurant store status and generates reports of uptime and downtime during business hours.

## Project Overview

The Store Monitoring System is a FastAPI-based service that analyzes store activity patterns and generates comprehensive reports on store uptime and downtime. The system processes store status observations, business hours, and timezone data to calculate accurate metrics for each store.

## Setup and Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application using one of the following methods:

   ```
   # Using the run.py script
   python run.py

   # Or using uvicorn directly
   uvicorn main:app --reload
   ```

   The application will run on http://localhost:5000 by default (or http://localhost:8000 if using uvicorn directly).

## System Architecture

The application consists of several key components:

### Data Models

- **StoreStatus**: Tracks store activity status (active/inactive) with timestamps
- **BusinessHours**: Defines when stores are expected to be open
- **StoreTimezone**: Stores timezone information for each store
- **Report**: Tracks report generation status and file paths

### API Endpoints

1. **Trigger Report Generation**

   - Endpoint: `/trigger_report`
   - Method: GET
   - Response: JSON with report_id
   - Description: Generates a unique report ID and starts a background task to process store data

   ```json
   {
     "report_id": "f8e7d65c-5678-4321-a123-456789abcdef"
   }
   ```

2. **Get Report Status/Download**

   - Endpoint: `/get_report?report_id=<report_id>`
   - Method: GET
   - Response:
     - If report is still running: `{"status": "Running"}`
     - If report is complete: Returns the CSV file as a download
     - If report not found: 404 error
     - If report failed: 500 error

3. **Root Endpoint**
   - Endpoint: `/`
   - Method: GET
   - Response: Welcome message with API documentation and endpoint information

## API Usage with cURL

You can interact with the API using cURL commands:

1. **Trigger a report generation**:

   ```bash
   curl -X GET "http://localhost:8000/trigger_report"
   ```

2. **Check report status or download the report** (replace `REPORT_ID` with the actual report ID):

   ```bash
   curl -X GET "http://localhost:8000/get_report?report_id=REPORT_ID" --output report.csv
   ```

3. **Get API information**:
   ```bash
   curl -X GET "http://localhost:5000/"
   ```

Note: If you're using uvicorn directly with the default port, use port 8000 instead of 5000 in the above commands.

## Data Flow

1. **Initialization**:

   - On startup, the system creates database tables if they don't exist
   - CSV data is imported into an SQLite database (`store_monitor.db`)
   - Large datasets are processed in batches to manage memory usage

2. **Report Generation**:

   - A user triggers report generation via the API
   - A background task processes all stores:
     - Retrieves store timezone and business hours information
     - Calculates uptime/downtime for the last hour, day, and week
     - Outputs results to a CSV file

3. **Report Retrieval**:
   - Users can check report status and download completed reports using the report ID

## Data Sources

The system processes data from three CSV files:

- **store_status.csv**: Contains periodic observations of store activity status

  - `store_id`: Unique identifier for each store
  - `timestamp_utc`: Time of observation in UTC
  - `status`: Store status ("active" or "inactive")

- **menu_hours.csv**: Contains business hours information

  - `store_id`: Unique identifier for each store
  - `dayOfWeek`: Day of week (0=Monday, 6=Sunday)
  - `start_time_local`: Local opening time
  - `end_time_local`: Local closing time

- **timezones.csv**: Contains store timezone information
  - `store_id`: Unique identifier for each store
  - `timezone_str`: Timezone string (e.g., "America/Chicago")

## Report Output Format

The generated report is a CSV file with the following columns:

- `store_id`: Unique identifier for each store
- `uptime_last_hour(in minutes)`: Store uptime in the last hour, in minutes
- `uptime_last_day(in hours)`: Store uptime in the last day, in hours
- `update_last_week(in hours)`: Store uptime in the last week, in hours
- `downtime_last_hour(in minutes)`: Store downtime in the last hour, in minutes
- `downtime_last_day(in hours)`: Store downtime in the last day, in hours
- `downtime_last_week(in hours)`: Store downtime in the last week, in hours

## Algorithm for Uptime and Downtime Calculation

The core algorithm for calculating uptime and downtime involves:

1. **Business Hours Handling**:

   - For each store, business hours are determined from the data
   - If no business hours data is available, the store is assumed to be open 24/7
   - Timezone conversion ensures accurate business hour comparisons

2. **Observation Processing**:

   - Status observations are retrieved for each time interval (hour, day, week)
   - Gaps between observations are handled through status interpolation
   - For sparse data, status is extrapolated based on available observations

3. **Time Period Calculations**:
   - Only business hours are considered when calculating uptime/downtime
   - The system handles special cases like business hours spanning midnight
   - Results are converted to appropriate units for reporting

## Performance Considerations

- The system processes data in batches to manage memory usage
- Database indexes are used to improve query performance
- Background tasks prevent API blocking during report generation

## Improvement Ideas

1. **Optimization**: Implement more efficient data processing for larger datasets through parallel processing.

2. **Caching**: Implement caching mechanisms to store frequently accessed data (like business hours and timezones) to reduce database queries.

3. **Database Indexing**: Add more specialized indexes to improve query performance for specific operations.

4. **Asynchronous Processing**: Implement a proper task queue system (like Celery with Redis) for handling report generation asynchronously, which would be more robust than the current threading approach.

5. **Frontend Interface**: Add a simple web interface for users to trigger reports and view results.

6. **Testing**: Add comprehensive unit and integration tests to ensure reliability.

7. **API Documentation**: Add Swagger/OpenAPI documentation for the API endpoints.

## Sample Output

A sample report output looks like:

```
store_id,uptime_last_hour(in minutes),uptime_last_day(in hours),update_last_week(in hours),downtime_last_hour(in minutes),downtime_last_day(in hours),downtime_last_week(in hours)
00017c6a-7a77-4a95-bb2d-40647868aff6,60.0,6.45,75.5,0.0,4.05,0.0
000bba84-20af-4a8b-b68a-368922cc6ad1,0,0.0,0.0,60.0,24.0,168.0
...
```

## Future Improvements

While the current implementation meets all the requirements, there are several ways this solution could be enhanced for a production environment:

### Performance Optimizations

- Implement parallel processing using `concurrent.futures` to process multiple stores simultaneously, reducing report generation time
- Use caching mechanisms for frequently accessed data (e.g., Redis) to reduce database load
- Consider using a more robust database like PostgreSQL for larger datasets and better query performance
- Implement database indexing strategies optimized for time-series data
- Use database connection pooling to handle higher concurrency

### Enhanced Features

- Add a dashboard UI to visualize uptime/downtime metrics with interactive charts
- Implement real-time notifications for store owners when stores go offline
- Add filters to the API to generate reports for specific stores or time periods
- Implement export options in different formats (JSON, Excel, PDF)
- Add historical trend analysis for store performance over time

### Architecture Improvements

- Implement a message queue system (e.g., RabbitMQ, Kafka) for more robust background processing
- Create a microservices architecture to separate data ingestion from report generation
- Containerize the application using Docker for easier deployment and scaling
- Use Kubernetes for orchestration in a production environment
- Implement API versioning to support backward compatibility

### Monitoring and Observability

- Integrate logging and monitoring tools (e.g., Prometheus, Grafana)
- Add application health checks and metrics endpoints
- Implement automated alerts for slow report generation or system issues
- Add tracing for performance bottlenecks using tools like Jaeger or Zipkin
- Create operational dashboards for system health visualization

### Data Handling

- Implement a data versioning system to track changes in store status over time
- Add data validation and cleansing steps for CSV imports
- Create a dedicated ETL pipeline for more robust data loading
- Implement data partitioning for improved query performance
- Add data retention policies to manage database growth

### Security Enhancements

- Add authentication and authorization for API endpoints
- Implement rate limiting to prevent API abuse
- Add data encryption for sensitive information
- Implement audit logging for all data access
- Add CORS policies and security headers

### Testing and CI/CD

- Expand test coverage with unit and integration tests
- Set up automated CI/CD pipelines for continuous deployment
- Add performance benchmark tests to catch regressions
- Implement load testing to ensure the system can handle peak traffic
- Add automated security scanning in the CI/CD pipeline

### Documentation

- Create comprehensive API documentation using tools like Swagger/OpenAPI
- Add developer guides for code contributions
- Document data models and business logic for better maintainability
- Create user guides for store owners and administrators
- Add sequence diagrams for complex workflows
