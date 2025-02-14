# Auto Service Management API

A Flask-based REST API for managing an auto service center, including customers, mechanics, service tickets, and inventory management.

## Features

- User authentication with JWT tokens
- Rate limiting for API endpoints
- Response caching for improved performance
- CRUD operations for:
  - Users/Customers
  - Service Tickets
  - Mechanics
  - Inventory/Parts
- Relationship management between entities
- Pagination for list endpoints
- Error handling and validation

## Project Structure

```
SE_Advanced-API-Development_V2/
├── app/
│   ├── components/
|   │   ├── blueprints/
|   │   │   ├── users/
|   │   │   │   ├── __init__.py
|   │   │   │   └── routes.py
|   │   │   ├── mechanics/
|   │   │   │   ├── __init__.py
|   │   │   │   └── routes.py
|   │   │   ├── service_tickets/
|   │   │   │   ├── __init__.py
|   │   │   │   └── routes.py
|   │   │   └── inventory/
|   │   │       ├── __init__.py
|   │   │       └── routes.py
|   │   └── schemas/
|   │       ├── __init__.py
|   │       ├── inventory.py
|   │       ├── mechanic.py
|   │       ├── service_ticket.py
|   │       └── user.py
|   ├── static/
|   │   └── swagger.yaml
|   ├──utils/
│   │   └── util.py
│   ├── extensions.py
│   └── models.py
├── instance/
│   └── app.db
├── .env
├── app.py
├── collection.json
├── config.py
├── README.md
└── requirements.txt
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/MatthewGUser/SE_Advanced-API-Development_V2.git
cd SE_Advanced-API-Development_V2
```

2. Create and activate virtual environment:

```
python -m venv venv
.\venv\Scripts\activate
```

3. Install dependencies:

```
pip install -r requirements.txt
```

4. Set up environment variables:

```
set FLASK_APP=app.py
set FLASK_ENV=development
```

## Running the Application

```
python app.py
```

The API will be available at
`http://localhost:5000`

## API Endpoints

### Users

- `GET /users?page=1&per_page=10` - List all users (paginated)
- `GET /users/my-tickets` - Get user's service tickets
- `POST /users/register` - Register new user
- `POST /users/login` - User login
- `PUT /users/<id>` - Update user
- `DELETE /users/<id>` - Delete user

### Service Tickets

- `GET /service-tickets?page=1&per_page=10` - List tickets (paginated)
- `GET /service-tickets/<id>` - Get single ticket
- `POST /service-tickets` - Create ticket
- `PUT /service-tickets/<id>` - Update ticket
- `DELETE /service-tickets/<id>` - Delete ticket

### Mechanics

- `GET /mechanics?page=1&per_page=10` - List mechanics (paginated)
- `GET /mechanics` - List mechanics
- `POST /mechanics` - Add mechanic
- `PUT /mechanics/<id>` - Update mechanic
- `DELETE /mechanics/<id>` - Delete mechanic

### Inventory

- `GET /inventory?page=1&per_page=10` - List parts (paginated)
- `GET /inventory` - List parts
- `POST /inventory` - Add part
- `PUT /inventory/<id>` - Update part
- `DELETE /inventory/<id>` - Delete part

## Authentication

The API uses JWT tokens for authentication. Include the token in requests:

## Rate Limiting

Endpoints are rate-limited to prevent abuse:

- Login: 5 requests per minute
- Registration: 3 requests per hour
- Other endpoints: 30 requests per minute

## Caching

List endpoints are cached for 5 minutes to improve performance.

## Error Handling

The API returns appropriate HTTP status codes and error messages:

- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error
