
# Axon Pharmacy | Function Calling With LLM

This is an app that allows admin to generate and post announcements to Telegram channels and groups, add medicines to the database, update stock, delete medicines, and update order status. It also allows users to search for medicines, view medicine details, place orders, view order status, and cancel orders. All done with just a random prompt to Gemini AI.

Here is how it works:
![How the function calling works?](assets/image.png)

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
## Tech Stack
- Python
- Jupyter Notebook
- Streamlit
- Firebase
- Gemini AI
- Telegram API
- Telegram Bot Integration
- API Integration
- Database Management

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
```

## Features

### Admin Application (`admin.py`)
- **Login:** Admin login with email and password.
- **Generate Announcement:** Create and post pharmacy announcements to Telegram channel and group using Gemini AI.
- **Add Medicine:** Add new medicine entries to the Firebase database.
- **Update Stock:** Modify the stock quantity of existing medicines and notify users if a medicine is out of stock via Telegram.
- **Delete Medicine:** Remove medicine entries from the database and send Telegram notifications.
- **Update Order Status:** Change the status of customer orders in Firebase.

### User Application (`app.py`)
- **Search Medicines Availability:** Search for medicines by name or category.
- **Place Order:** Place a new order for a medicine.
- **Cancel Order:** Cancel a pending or processing order.
- **View Order Status:** Check the status of your order.
- **Get Professional Advice:** Get advice from the llm based on his symptoms and profile details and order status.

#### Key Insights and Ouptuts
- **Streamlit:** Streamlit is a Python library for building interactive web applications.
- **Firebase:** Firebase is a platform for building and deploying apps, databases, and other cloud services.
- **Gemini AI:** Gemini AI is a platform for building and deploying LLMs.
- **Telegram:** Telegram is a messaging and voice communication platform.

This is a demo for How LLMs are powerful in automating pharmacy services. Take a look at in the sample output below that the model has done for the Pharmacy Admin...

![Sample Output-1](assets\parallel_calling.jpg)
- Here was the prompt given to the model 
```
write a telegram announcement regarding this that a new medicine 
using telegram_post function called paracetamol is arrived and 
record this medicine, and add 200 stock to the aspirin medicine, 
and delete the asprin medicine since it is prohibited by the 
government, and update the order status of order 
0b527cd538844e7ab93c4f656f314cd7 to delivered.
```

![Sample Output-2](assets\parallel_calling1.jpg)

It has been be able to call multiple functions at the same time.