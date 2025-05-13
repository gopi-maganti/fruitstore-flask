# 🍎 Fruit Store API - Flask Backend

This is a backend API for an online fruit store built with **Flask**, **SQLAlchemy**, **Pydantic**, and **Swagger** documentation. It supports functionalities like user registration, fruit inventory management, cart operations, and order placement.

---

## 🚀 Features

- Add/view/update/delete fruits (with image upload support)
- Register and manage users
- Add/update/remove cart items
- Place grouped orders and view order history
- Guest checkout supported via `user_id = -1`
- Swagger API documentation
- SQLite as default DB (can be swapped for PostgreSQL, etc.)
- CORS enabled for frontend integration

---

## 📁 Project Structure

```
fruitstore-backend/
│
├── app/
│   ├── apis/                # API route blueprints
│   ├── models/              # SQLAlchemy ORM models
│   ├── schemas/             # Pydantic request validations
│   ├── __init__.py          # Flask app factory
│
├── static/uploads/          # Image upload directory
├── config.py                # Configuration (e.g., DB path, upload folder)
├── run.py                   # Entry point to start the server
└── requirements.txt         # Python dependencies
```

---

## ⚙️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/fruitstore-backend.git
cd fruitstore-backend

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🧪 Running the App

```bash
# Start the Flask server
python run.py
```

Access the Swagger docs at: [http://localhost:5000/apidocs](http://localhost:5000/apidocs)

---

## 🐳 Docker Support

If you want to run this with Docker:

```bash
docker build -t fruitstore-backend .
docker run -p 5000:5000 fruitstore-backend
```

> Note: Make sure your Dockerfile and volume paths handle the `static/uploads` folder for image storage.

---

## 📦 API Endpoints

Base URL: `http://localhost:5000`

### 🍇 Fruit
- `POST /fruit/add` — Add fruit with image (multipart/form-data)
- `GET /fruit/` — Get all fruits
- `GET /fruit/<id>` — Get fruit by ID
- `PUT /fruit/<id>` — Update fruit info (price, quantity, etc.)
- `DELETE /fruit/<id>` — Delete a fruit

### 👤 User
- `POST /user/add` — Register user
- `GET /user/` — List all users
- `GET /user/<id>` — Get user details
- `DELETE /user/<id>` — Delete user

### 🛒 Cart
- `POST /cart/add` — Add item to cart
- `GET /cart/<user_id>` — Get all cart items for a user
- `PUT /cart/update/<cart_id>` — Update item quantity
- `DELETE /cart/delete/<cart_id>` — Delete an item
- `DELETE /cart/clear/<user_id>` — Clear entire cart
- `POST /cart/associate-cart` — Link guest cart to registered user

### 📦 Orders
- `POST /order/add/<user_id>` — Place grouped order
- `GET /order/getall` — List all orders
- `GET /order/history/<user_id>` — Order history for a user

---

## 🔒 Validation

- Input validation handled using **Pydantic**
- Image uploads restricted to 10MB via `MAX_CONTENT_LENGTH`
- Phone numbers must be exactly 10 digits

---

## 🛠️ Tech Stack

- Python 3.10+
- Flask
- SQLAlchemy
- Pydantic
- Flasgger (Swagger UI)
- SQLite (default DB)
- CORS

---

## 📬 Feedback / Contributing

PRs and issues are welcome! If you'd like to contribute, please fork and submit a pull request.

---

## 📄 License

MIT License — feel free to use and modify.