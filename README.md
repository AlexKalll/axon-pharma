![How the function calling works?](assets/image.png)


# Axon Pharmacy

This repository contains two Streamlit applications: one for general users (`app.py`) and one for administrators (`admin_app.py`).

## Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/alexkalll/axon-pharma.git
    cd axon-pharma
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables:**
    Create a `.env` file in the root directory and add the following (replace with your actual values):
    
    ```bash
    GEMINI_API_KEY=your_gemini_api_key
    TELEGRAM_BOT_TOKEN=your_telegram_bot_token
    CHANNEL_USERNAME=@your_telegram_channel_username
    GROUP_USERNAME=@your_telegram_group_username
    # Firebase credentials (if applicable, usually handled by firebase/db_manager.py)
    ```

## How to Run

### Run the User Application

To run the main user application, use the following command:

```bash
streamlit run app.py
```

### Run the Admin Application

To run the admin dashboard, use the following command:

```bash
streamlit run admin.py # to run the admin page in Streamlit
or 
streamlit run main.py  # to run the main functionality for the app users
```

## Features

### User Application (`app.py`)
- User login (authentication handled by `utils/auth.py`)
- Placeholder for general user functionalities.

### Admin Application (`admin_app.py`)
- Admin login (authentication handled by `utils/auth.py`)
- **Generate Announcement:** Create and post pharmacy announcements to Telegram channels/groups using Gemini AI.
- **Add Medicine:** Add new medicine entries to the Firebase database.
- **Update Stock:** Modify the stock quantity of existing medicines and notify users if a medicine is out of stock via Telegram.
- **Delete Medicine:** Remove medicine entries from the database and send Telegram notifications.
- **Update Order Status:** Change the status of customer orders in Firebase.

## ✅ Key Functional Features (Updated for Mobile E-commerce)

| Feature | Description | Involves | Gemini Function Calling? |
| ------- | ----------- | -------- | ------------------------ |

1. **Medicine Catalog with Search** | Browse and search medicines by name, category | Flutter + Laravel API | Optionally via `search_medicine()` |
2. **Order Placement (Cart + Checkout)** | Add to cart, checkout, place order | Laravel Orders API + MySQL | ✅ `order_medicine(med_name)` |
3. **Availability Check (LLM Chat)** | Ask “Is Amoxicillin available?” | Gemini routes to availability API | ✅ `check_availability()` |
4. **Smart Recommendations** | “What can I take for allergies?” → Suggested meds | Gemini symptom-based suggestion | ✅ `recommend_medicine(symptoms)` |
5. **Order Status & History** | View current + past orders | Flutter frontend, Laravel backend | ✅ `get_order_history()` |
6. **Admin Notifications via Telegram** | Notify admin when stock is low or order placed | Laravel + Telegram Bot | ✅ Triggered from LLM or backend |
7. **Auto Telegram Posts (Stock Updates)** | Post new stock or out-of-stock messages to Telegram channel | Laravel + Telegram Bot API | ✅ via `post_to_telegram(message)` |
8. **User Chat Assistant (Gemini)** | In-app chat that supports symptom help, FAQs, etc | Flutter chat UI + Gemini LLM | ✅ Core use |
9. **Push Notifications (Optional)** | Alert users when order is shipped, new offer, etc | Firebase Cloud Messaging | ✅ `send_notification(user_id, message)` |
10. **Pharmacy Contact & Location Info** | Show phone, map, and working hours | Static or from DB | ✅ Shared during function call |

---

## 🧱 Updated Tech Stack

| Layer         | Tool                                 | Notes                                         |
| ------------- | ------------------------------------ | --------------------------------------------- |
| Frontend      | **Flutter**                          | Android                              |
| Backend       | **Laravel (PHP)**                    | API for login, orders, stock, LLM integration |
| Database      | **MySQL (XAMPP)**                    | Medicines, Orders, Users, Search logs         |
| LLM           | **Google Gemini + Function Calling** | Handles smart queries via APIs                |
| Notifications | **Telegram Bot API**                 | For admin alerts                              |
| Hosting       | Localhost or Ngrok (for demo)        | Expose Laravel APIs for Gemini & Flutter      |
| Optional      | Firebase FCM                         | Push notifications to users                   |

---

## 📱 Flutter App Pages

| Page                  | Description                                   |
| --------------------- | --------------------------------------------- |
| Home                  | Featured medicines, search bar, categories    |
| Medicine Detail       | Image, price, description, availability       |
| Cart & Checkout       | Add/remove items, place order                 |
| My Orders             | View past orders & track status               |
| Chat Assistant        | Ask questions, place quick orders via Gemini  |
| Admin Mode (Optional) | For internal testing of posting/stock updates |

---

## 📡 Laravel API Endpoints

| Endpoint                      | Function                                          |
| ----------------------------- | ------------------------------------------------- |
| `POST /api/order-medicine`    | Gemini calls this to place order and notify admin |
| `GET /api/check-availability` | Gemini or Flutter checks for stock                |
| `GET /api/recommend`          | Gemini queries this with symptoms                 |
| `POST /api/telegram-post`     | Sends formatted message to Telegram bot           |
| `GET /api/medicines`          | List medicines with filters/search                |
| `POST /api/orders`            | Place a new order                                 |
| `GET /api/orders/user/:id`    | Get user order history                            |

---

## 🧠 Scoring Strategy (Still Targeting 10/10)

| Evaluation Category    | What You’re Delivering                                        |
| ---------------------- | ------------------------------------------------------------- |
| ✅ Function Calling     | LLM routes to Laravel API with multiple tools                 |
| ✅ API Integration      | Telegram Bot API, full REST Laravel API                       |
| ✅ DB Management        | Orders, users, medicines, search history                      |
| ✅ Real-world use       | Mobile pharmacy shopping app with chat + automation           |
| ✅ Clarity & Modularity | Flutter pages, Laravel controllers, Gemini tool schema        |
| ✅ Presentation         | Mobile demo + slides explaining flow (can help you prep this) |

---

## ✅ Immediate Next Steps

1. ✅ Set up your MySQL DB schema (`users`, `orders`, `medicines`, `chats`, etc.)
