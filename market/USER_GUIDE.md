# UofG UNIMarket — User Guide

## Table of Contents
1. [Getting Started](#1-getting-started)
2. [Customer Features](#2-customer-features)
3. [Seller Features](#3-seller-features)
4. [Staff / Admin Features](#4-staff--admin-features)
5. [Real-time Chat](#5-real-time-chat)
6. [Other Features](#6-other-features)
7. [Admin Account Information](#7-admin-account-information)

---

## 1. Getting Started

### Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Seed product categories
python manage.py shell -c "
from market.models import Category
for name in ['General','Dairy','Bakery','Beverages','Snacks','Fruits','Vegetables','Frozen','Stationery','Other']:
    Category.objects.get_or_create(name=name)
"

# Create a staff admin account
python manage.py createstaff admin Staff2025! --email admin@uni.ac.uk

# Start the server
python manage.py runserver
```

Open your browser and navigate to **http://127.0.0.1:8000/**.

### Registering a Customer Account

1. Go to the landing page and click **Register**.
2. Fill in your username, email, and password (minimum 8 characters, must contain at least one letter and one digit).
3. After registration, a verification email is sent to the console (development mode). Copy the verification link and open it in your browser.
4. Once verified, you can log in at `/login/`.

### Logging In

- **Customer:** Go to `/login/` and enter your email and password.
- **Staff:** Go to `/staff/login/` and enter your email and password.

---

## 2. Customer Features

### Browsing Products

- Navigate to **Products** from the sidebar.
- Use the **search bar** to search by product name.
- Use the **category dropdown** to filter by category (General, Dairy, Bakery, Beverages, Snacks, Fruits, Vegetables, Frozen, Stationery, Other).
- Products that have been delisted by staff will not appear in the catalogue.

### Shopping Cart & Placing Orders

1. Click **Add to Cart** on any product (the quantity is limited to available stock).
2. The cart icon in the top-right corner shows your current cart items.
3. Open the cart panel, review items and quantities, then click **Place Order**.
4. After placing an order, the status will be **Pending**.

### Confirming Receipt

1. Go to **My Orders** from the sidebar.
2. For orders with status **Pending**, click the **Confirm Receipt** button.
3. The order status changes to **Completed** (displayed as "Finished").
4. The seller is notified automatically.

### Favourites

- On the product listing, click the heart icon to add a product to your favourites.
- View all favourites from the **Favourites** page in the sidebar.
- Click again to remove from favourites.

### Requesting a Refund

1. Go to **My Orders**.
2. Click **Request Refund** on the relevant order item.
3. Enter a reason and select the quantity to refund.
4. The refund request will be sent to staff for review.
5. Track your refund status on the **My Refunds** page.

### Notifications

- A bell icon in the top navigation shows unread notification count.
- Click the bell to see a dropdown of recent notifications.
- Notifications are sent when:
  - Your order status changes.
  - A refund request is approved or rejected.
  - Your product is delisted or relisted by staff.
- Click a notification to mark it as read and navigate to the related page.

---

## 3. Seller Features

Every registered customer can also be a seller.

### Publishing a Product

1. From the **Dashboard** (home page), find the **Publish a Product** form.
2. Fill in: Product Name, Category, Price, Stock Quantity, Description (optional), and Product Image (optional).
3. Click **Publish Product**.
4. Your product will appear in the **My Published Products** section below.

### Managing Published Products

- **Edit:** Click the pencil icon to edit a product's name, category, price, stock, description, or image. The publish form transforms into an edit form.
- **Delete:** Click the trash icon to delete a product. Products that have been ordered cannot be deleted (set stock to 0 instead).
- **Sold indicator:** Products that have been included in completed orders show a green **Sold** badge and become locked (no edit/delete).
- **Delisted indicator:** If staff delists your product, a red **Delisted by Staff** badge appears. The product is hidden from the catalogue until staff relists it.

### Seller Statistics

- On the Dashboard, the **Account Status** section shows:
  - Total orders placed
  - Total spent
  - Products published
  - Favourites count
  - **Revenue** earned from sales
  - **Items Sold** count

---

## 4. Staff / Admin Features

Staff accounts can only be created from the local server using the management command:

```bash
python manage.py createstaff <username> <password> --email <email>
```

### Staff Dashboard

After logging in at `/staff/login/`, the staff dashboard provides quick access to:
- Order Management
- Inventory Management
- Customer Chat
- Refund Management

### Order Management

- Go to **Orders** from the staff sidebar.
- View all customer orders with status, date, and total.
- Change order status using the action dropdown (Pending, Processing, Completed, Cancelled).
- Customers are automatically notified of status changes.
- **Export CSV:** Click the "Export CSV" button to download all orders as a CSV file.

### Inventory Management

- Go to **Inventory** from the staff sidebar.
- View all products with ID, name, category, price, stock, and active status.
- **Adjust Stock:** Enter a quantity and click **In** (add stock) or **Out** (remove stock).
- **Delist Product:** Click the red **Delist** button to hide a product from the catalogue. The seller is automatically notified.
- **Relist Product:** Click the green **Relist** button to make a delisted product visible again.
- Delisted products are shown with a grey background and a red "Delisted" badge.
- **Export CSV:** Click "Export CSV" to download inventory data including active/delisted status.

### Refund Management

- Go to **Refunds** from the staff sidebar.
- Filter refund requests by status: All, Pending, Approved, Rejected.
- Click **Approve** or **Reject** on pending requests.
- Approving a refund restores stock and sets the order status to Cancelled.
- The customer is automatically notified of the decision.

### Customer Support Chat

- Go to **Chat** from the staff sidebar.
- The sidebar shows individual support conversations for each customer (e.g., "Support: Ganjinyu").
- Click a customer's support room to view and reply to their messages.
- Staff can only see support rooms, not private buyer-seller chats.

---

## 5. Real-time Chat

UNIMarket uses WebSocket technology for instant messaging.

### Customer Support

1. Click **Start Chat** from the dashboard, or go to **Chat** from the sidebar.
2. You will automatically enter your private **Customer Support** room.
3. Send a message and wait for a staff member to reply.
4. Messages are persisted and available when you return later.
5. Each customer has their own private support room. Other customers cannot see your messages.

### Chat with Sellers

1. On the **Products** page, click **Chat with Seller** on any product.
2. This opens a private chat room for that specific product.
3. The Chat Info panel on the right shows the product name, image, and product code.
4. If you buy multiple products from the same seller, each product gets its own chat room.
5. You cannot chat with yourself (your own products show a disabled chat button with a tooltip).

### Chat Features

- **Typing indicator:** When the other person is typing, you see "[user] is typing..." below the chat.
- **Message history:** The last 50 messages are loaded when you enter a room.
- **Delete chat:** Click the red X button on any chat room (except support) to delete the conversation.
- **Room sidebar:** All your conversations appear in the left sidebar with the last message preview.

---

## 6. Other Features

### Dark Mode

- Click the moon/sun icon in the navigation bar to toggle dark mode.
- Your preference is saved in the browser and persists across sessions.

### Print Invoice

- On the Orders page, orders include a print-friendly layout.
- Use your browser's print function to generate an invoice.

### Email Verification (Development)

- In development mode, verification emails are printed to the server console.
- Copy the verification URL from the console output and open it in your browser.

### Password Requirements

- Minimum 8 characters
- At least one letter
- At least one digit

### Rate Limiting

- After 5 failed login attempts, the account is locked for 5 minutes.

---

## 7. Admin Account Information

### Default Staff Account

| Field       | Value                |
|-------------|----------------------|
| **Username** | `admin`             |
| **Email**    | `admin@uni.ac.uk`   |
| **Password** | `Staff2025!`        |
| **Login URL** | `http://127.0.0.1:8000/staff/login/` |

### Creating Additional Staff Accounts

Staff accounts can **only** be created from the local server (127.0.0.1). External IP addresses cannot register staff accounts.

```bash
# Using the management command (recommended)
python manage.py createstaff <username> <password> --email <email>

# Examples
python manage.py createstaff alice Alice2025! --email alice@uni.ac.uk
python manage.py createstaff bob Bob2025!     # email defaults to bob@unimarket.staff
```

### Django Admin Panel

Access the built-in Django admin at `/admin/` for direct database management. You will need to create a Django superuser first:

```bash
python manage.py createsuperuser
```

This provides access to all models: Customer, Staff, Product, Order, OrderItem, Favourite, RefundRequest, Notification, Category, ChatMessage.
