# E-commerce Web Application

**Second Partial Exam – Multimedia Design and Production**  
University of Florence – 2025

**Autore:** Guido Rossi

## Description

This project is designed to offer a structure for online stores with core features like product browsing, user authentication, shopping cart, and order management.

TODO: rimuovi questo
Questa applicazione web consente agli utenti di esplorare e acquistare prodotti in un negozio online implementando .
Gli utenti possono visualizzare i dettagli dei prodotti, aggiungerli al carrello e procedere con l'acquisto. 
I prodotti possono essere filtrati per categoria o brand e possono essere cercati per nome.

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

### Account Credentials

- **Admin Account:**
  - Username: admin
  - Password: admin

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

- The **User model is extended and customized** to include additional fields such as saved addresses, profile data, and group-based permissions.

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
