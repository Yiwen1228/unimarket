# UofG UNIMarket

A full-featured university marketplace web application built for the University of Glasgow. Students can buy and sell products, chat in real time with sellers and support staff, manage orders, request refunds, and more.

## Tech Stack

- **Backend:** Django 5.2 (LTS), Django REST Framework 3.15
- **Real-time:** Django Channels 4.0, Daphne 4.0 (ASGI / WebSocket)
- **Database:** SQLite 3 (development)
- **Frontend:** Bootstrap 5.3, Bootstrap Icons, vanilla JavaScript
- **Auth:** Session-based (custom Customer / Staff models with hashed passwords)

## Features

### Customer
- Register & log in (with email verification)
- Browse, search and filter products by category
- Shopping cart, place orders, confirm receipt
- Publish / edit / delete your own products
- Favourite products
- Real-time chat with sellers (per-product private rooms)
- Private customer-support chat with staff
- Request refunds on orders
- Notification bell (real-time unread count)
- Dark mode toggle
- Seller statistics dashboard (revenue, items sold)

### Staff / Admin
- Force delist (and relist) any product
- Manage inventory (stock in / out)
- Update order status
- Approve or reject refund requests
- Customer-support chat (separate room per customer)
- CSV export for orders and inventory
- Staff accounts can **only** be created from the local server

## Prerequisites

- Python 3.10+
- pip

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/<your-org>/unimarket.git
cd unimarket

# 2. Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Apply database migrations
python manage.py migrate

# 5. Seed default product categories
python manage.py shell -c "
from market.models import Category
for name in ['General','Dairy','Bakery','Beverages','Snacks','Fruits','Vegetables','Frozen','Stationery','Other']:
    Category.objects.get_or_create(name=name)
print('Categories seeded.')
"

# 6. Create an initial staff account
python manage.py createstaff admin Staff2025! --email admin@uni.ac.uk

# 7. Run the development server (Daphne ASGI)
python manage.py runserver
```

The application will be available at **http://127.0.0.1:8000/**.

## Default Staff Account

| Field    | Value              |
|----------|--------------------|
| Email    | `admin@uni.ac.uk`  |
| Password | `Staff2025!`       |
| Login URL | `/staff/login/`   |

> Staff registration is restricted to requests originating from `127.0.0.1` / `::1` / `localhost`.

## Project Structure

```
unimarket/
├── core/                   # Django project settings, ASGI config
│   ├── settings.py
│   ├── urls.py
│   └── asgi.py
├── market/                 # Main application
│   ├── models.py           # Customer, Staff, Product, Order, Chat, etc.
│   ├── views.py            # Template-based views
│   ├── api_views.py        # REST API endpoints
│   ├── serializers.py      # DRF serializers
│   ├── consumers.py        # WebSocket consumer (real-time chat)
│   ├── routing.py          # WebSocket URL routing
│   ├── urls.py             # Template URL patterns
│   ├── api_urls.py         # API URL patterns
│   ├── admin.py            # Django admin registration
│   ├── templates/market/   # HTML templates
│   ├── static/market/      # CSS & JavaScript
│   └── management/commands/ # Custom management commands
├── media/                  # User-uploaded images
├── requirements.txt
├── manage.py
└── db.sqlite3              # SQLite database (dev)
```

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/customer/register/` | Register customer |
| POST | `/api/customer/login/` | Customer login |
| POST | `/api/staff/login/` | Staff login |
| POST | `/api/logout/` | Logout |
| GET  | `/api/verify/?token=` | Email verification |

### Products
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/products/` | List / search / filter products |
| POST | `/api/products/publish/` | Publish a new product |
| GET  | `/api/products/my/` | My published products |
| PATCH | `/api/products/<id>/` | Update product |
| DELETE | `/api/products/<id>/delete/` | Delete product |
| GET  | `/api/categories/` | List categories |

### Orders
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders/` | Place order |
| GET  | `/api/orders/my/` | My orders |
| PATCH | `/api/orders/<id>/confirm/` | Confirm receipt |

### Staff
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | `/api/staff/orders/` | All orders |
| PATCH | `/api/staff/orders/<id>/` | Update order status |
| GET  | `/api/staff/inventory/` | Inventory list |
| PATCH | `/api/staff/inventory/<id>/` | Adjust stock |
| PATCH | `/api/staff/inventory/<id>/toggle-active/` | Delist / relist product |
| GET  | `/api/staff/refunds/` | Refund requests |
| PATCH | `/api/staff/refunds/<id>/` | Approve / reject refund |

### WebSocket
```
ws://<host>/ws/chat/<room_name>/
```
Room naming: `support_c<id>` (customer support), `seller<id>p<pid>` (product chat).

## Running Tests

```bash
python manage.py test market
```

## License

This project was developed as coursework for the University of Glasgow IT Project module.
