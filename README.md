# E-commerce Web Application

[![Python](https://img.shields.io/badge/python-3.12.11-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2.3-green?logo=django)](https://www.djangoproject.com/)

**Second Partial Exam – Multimedia Design and Production**  
University of Florence – 2025

**Autore:** Guido Rossi

## Description

This project is designed to offer a structure for online stores with core features like product browsing, user authentication, shopping cart, and order management.

### Features

- **Product browsing:** View product details including name, description, price, image, category, and brand.
- **User authentication:** Register and log in to your account securely.
- **Shopping cart:** Add and remove items, view cart contents, and proceed to checkout.
- **Coupon system:** Apply discount codes during checkout.
- **Address system:** Form for shipping address at checkout. If available, the last used or saved address is suggested automatically.
- **Order management:** View your order history and detailed breakdown (price, discounts, products, shipping status).
- **Admin panel:** Full management of products, categories, brands and orders.
- **Search functionality:** Search for products by name.
- **Product filtering:** Filter by category or brand for easier browsing.

### Technologies Used

- **Frontend:** HTML, CSS, JavaScript, Bootstrap
- **Backend:** Python, Django
- **Database:** SQLite (development), Supabase (production)
- **Image Storage:** Cloudinary
- **Deployment:** Render

### Deployment

- https://ecommerce-p9h8.onrender.com/

### Demo Credentials

- **Admin Account:**
  - Username: admin
  - Password: admin

- **Coupon Code:**
  - SUMMER5

### Environment Configuration

The project uses the `ENV` variable to switch between development and production environments.
This allows for different settings such as databases and installed apps, depending on the context in which the project is run.

- When ENV = `development`: 
  - Uses SQLite as the database (local file db.sqlite3)
  - Faster performance locally as no external services are required.
- When ENV = `production`:
  - Uses PostgreSQL (e.g., Supabase) as the database via DATABASE_URL
  - Enables additional third-party apps such as:
    1. cloudinary
    2. cloudinary_storage

## Project Requirements

This project has been developed to meet the functional and structural criteria defined in the exam guidelines.

- The **backend** includes **three distinct Django apps**:  
  - `store`: Manages products, categories, brands, orders, and coupons.  
  - `users`: Handles registration, login, and custom user profiles.
  - `orders`: Manages order history and details.

- **Model relationships** are implemented as follows:  
  - Products belong to a category and a brand (ForeignKey relationships).  
  - Orders are linked to users and contain multiple products (ManyToMany with through model). 

- At least **one view uses Django’s class-based generic views**, for example:  
  - The product detail page uses `DetailView` to render individual product data dynamically.

- **Two different permission levels** are defined using Django’s group system:  
  - **Customers**: Can browse, purchase, and view their own orders.  
  - **Store managers**: Have access to the admin panel to manage products, categories, brands and orders.

- The **User model is extended and customized** to include additional fields such as saved addresses and phone number.

## Extra Features

- **Coupon management**  
  Users can enter coupon codes during checkout to receive discounts.  
  Coupons are created and managed from the admin panel.

- **Address suggestion system**  
  During checkout, the system automatically suggests the last shipping address used or a saved address from the user’s profile.

- **Resilient order display**  
  Orders remain visible in the user’s order history even if a previously ordered product has been deleted from the catalog.

- **Automatic cart cleanup**  
  If a product in the shopping cart has been deleted from the store, it is automatically removed to prevent invalid purchases.

## Setup

1. **Clone the repository**

```bash
git clone https://github.com/guido-7/ecommerce.git
```

2. **Create the environment file**

Before running the project, copy the provided environment configuration file and customize it:
 
```bash
cp example.env .env
```

Edit `.env` with your own values.

3. **Create and activate a virtual environment**

```bash
conda create --name ecommerce-env
conda activate ecommerce-env
```

4. **Install dependencies**

```bash
pip install -r requirements.txt
```

5. **Run migrations**

```bash
python manage.py migrate
python manage.py runserver
```