# CT Scan Centers Dashboard

A comprehensive dashboard for visualizing CT scan centers across Maharashtra, India with interactive maps and data analytics.

## Features

- Interactive India map visualization showing CT scan center locations
- City-wise data organization with drill-down capabilities
- Contact information and Google Maps integration
- Data deduplication and validation features
- CSV upload functionality for easy data management
- Comprehensive analytics and reporting

## Prerequisites

Choose one of the following approaches:

### Option 1: Manual Installation (Traditional Method)
- Python 3.8+
- Node.js 14+
- npm 6+

### Option 2: Docker Installation (Containerized Method)
- Docker and Docker Compose
- Git (for cloning the repository)

## Quick Start Options

### Option 1: Manual Installation (Recommended for Development)

1. Clone the repository:
   ```bash
   git clone https://github.com/BiocliqAI/sales_compass.git
   cd sales_compass
   ```

2. Start the backend server:
   ```bash
   cd backend
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn main:app --host 0.0.0.0 --port 5050
   ```

3. In a new terminal, start the frontend development server:
   ```bash
   cd frontend
   npm install
   npm start
   ```

4. Access the application:
   - Frontend: http://localhost:3030
   - Backend API: http://localhost:5050

### Option 2: Docker Installation (Recommended for Deployment)

1. Clone the repository:
   ```bash
   git clone https://github.com/BiocliqAI/sales_compass.git
   cd sales_compass
   ```

2. Start the application using Docker Compose:
   ```bash
   docker compose up --build
   ```
   or if you have the older docker-compose command:
   ```bash
   docker-compose up --build
   ```

3. Access the application:
   - Frontend: http://localhost:3030
   - Backend API: http://localhost:5050

4. To stop the application:
   ```bash
   docker compose down
   ```
   or:
   ```bash
   docker-compose down
   ```

## Manual Installation (Alternative)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Start the backend server:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 5050
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the frontend development server:
   ```bash
   npm start
   ```

## Environment Variables

Create a `.env` file in the `backend` directory with your Gemini API key:

```env
GEMINI_API_KEY=your_actual_api_key_here
DATABASE_URL=sqlite:///./ct_scan_centers.db
```

## Docker Configuration

The application uses Docker Compose with the following services:

- `backend`: FastAPI application serving the CT scan centers data
- `frontend`: React application providing the dashboard interface

### Ports

- Frontend: 3030
- Backend: 5050

## API Endpoints

- `GET /api/centers` - Retrieve all CT scan centers
- `POST /api/upload` - Upload CSV data
- `DELETE /api/deduplicate` - Remove duplicate records
- `PUT /api/cities/{city_name}/validate` - Validate/unvalidate all centers in a city
- `DELETE /api/centers/{center_id}` - Delete a specific center

## Data Structure

The application includes CSV data files for major cities in Maharashtra:
- Aurangabad
- Jalgaon
- Kolhapur
- Nagpur
- Nashik
- Pune
- Sangli

Each CSV file contains information about CT scan centers including:
- Center Name
- Address
- Contact Details
- Google Maps Link

## License

This project is proprietary and confidential to Biocliq Technologies.