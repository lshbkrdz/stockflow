# StockFlow

StockFlow is a real working inventory and order management demo application built for a developer portfolio.

It includes a React + TypeScript frontend, FastAPI backend, SQLite local database, REST API, simple demo authentication, seeded fake data, product CRUD, suppliers, orders, search/filtering, dashboard statistics, low-stock warnings, loading states, empty states, error handling, and responsive dark admin styling.

All seeded records are simulated demo data. They are not real client data, real orders, or real revenue.

## Project Structure

```text
stockflow/
|-- frontend/
|-- backend/
|-- requirements.txt
|-- .env.example
`-- README.md
```

## Demo Credentials

```text
Email: demo@stockflow.dev
Password: demo1234
```

## Backend Setup

From the `stockflow` folder:

```bash
python -m venv .venv
```

Activate the virtual environment on Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the FastAPI backend:

```bash
uvicorn backend.app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

The SQLite database is created automatically at:

```text
backend/stockflow.db
```

Seeded demo data is inserted automatically on startup if the database is empty.

## Frontend Setup

Open a second terminal and go to the frontend folder:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create a local frontend environment file:

```bash
copy .env.example .env
```

Run the React app:

```bash
npm run dev
```

The frontend will be available at:

```text
http://localhost:5173
```

## Running Tests

Backend tests:

```bash
pytest
```

Frontend production build check:

```bash
cd frontend
npm run build
```

## Core Features

- Demo login
- Product list
- Add products
- Edit products
- Delete products
- Stock quantity tracking
- Low-stock warnings
- Supplier list
- Orders list
- Search and filtering
- Dashboard statistics
- Seeded fake demo data
- Clear simulated-data notice
- Responsive layout
- API validation
- Error handling
- Loading states
- Empty states
- Basic backend tests

## API Overview

Public:

- `GET /health`
- `POST /auth/login`

Protected with `Authorization: Bearer <token>`:

- `GET /dashboard`
- `GET /products`
- `POST /products`
- `PUT /products/{product_id}`
- `DELETE /products/{product_id}`
- `GET /suppliers`
- `GET /orders`
- `POST /orders`
- `GET /meta/categories`
- `POST /admin/reset-demo-data`

## Environment Variables

Copy `.env.example` and adjust values if needed:

```text
STOCKFLOW_DATABASE=backend/stockflow.db
STOCKFLOW_DEMO_USERNAME=demo@stockflow.dev
STOCKFLOW_DEMO_PASSWORD=demo1234
STOCKFLOW_DEMO_TOKEN=stockflow-demo-token
STOCKFLOW_CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

Frontend:

```text
VITE_API_URL=http://localhost:8000
```

Do not commit secrets. The included credentials are only for the demo application.

## Deployment Notes

The project is structured so it can be deployed later:

- Backend: FastAPI app can run on Render, Railway, Fly.io, or a VPS.
- Database: SQLite is used for local development. PostgreSQL can be added later for production.
- Frontend: Vite build output can be deployed to Netlify, Vercel, Cloudflare Pages, or GitHub Pages.
- API URL: set `VITE_API_URL` to the deployed backend URL before building the frontend.

## Simulated Data Notice

StockFlow uses seeded fake data for portfolio demonstration:

- Suppliers are fictional.
- Customers are fictional.
- Orders are fictional.
- Stock quantities are simulated.
- Dashboard statistics are generated from seeded demo records.

The application features are real working software features, but the business data is not real.
