# Client-Aware WiFi RRM - React Frontend

This directory contains the modern React + Material UI frontend for the AI-Assisted WiFi RRM project.

## Requirements

- Node.js >= 18.x
- Existing FastAPI backend running on port 8000

## Installation

Navigate to this directory and install dependencies:

```bash
cd frontend
npm install
```

## Running the Application

To start the Vite development server:

```bash
npm run dev
```
The application will start on `http://localhost:5173`.

## Environment Variables and Mock Mode

This project supports a **Mock Data Mode** for UI development when the FastAPI backend or Simulator is unavailable.

A `.env` file should be present in the `frontend` directory:

```env
VITE_USE_MOCK_DATA=true
```

- **Mock Mode (`true`)**: The API service layer (`src/services/api.js`) will instantly return hardcoded JSON structures perfectly matching the backend schemas. No network requests are made to the backend. You can safely build UI without needing the SQLite database or Python server running.
- **Backend Mode (`false` or unset)**: The API service layer makes real Axios requests to `/api/*`. Vite (`vite.config.js`) will automatically proxy these to `http://localhost:8000` (FastAPI).

## Project Structure

- `public/`: Static assets.
- `src/components/`: Reusable UI components (Cards, Charts, etc.).
- `src/pages/`: Main view components (Overview, SystemStatus).
- `src/services/api.js`: Centralized Axios logic and Mock Data generator.
- `src/hooks/`: React Custom Hooks for data fetching and polling.
- `src/layouts/`: Base layouts (Navigation, Sidebar).
- `src/theme/`: Material UI dark theme configuration.
- `src/types/`: Backend schema definitions for reference.
- `src/config.js`: Central configuration values (e.g. Refresh Intervals).

## Troubleshooting

- **CORS Errors**: Ensure the frontend is being accessed via the Vite dev server (port `5173`). Vite's proxy will handle forwarding `/api` to the backend on port `8000`. Do not fetch `localhost:8000` directly from the frontend code.
- **Failed to fetch / Connection Refused**: Verify the FastAPI backend is running (`python run.py`) if `VITE_USE_MOCK_DATA` is set to `false`.
