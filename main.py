import streamlit as st
from google import genai
from google.genai import types
from firebase_admin import credentials, initialize_app, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import json
import uuid
import datetime
import os
import firebase_admin
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()

# --- Firebase Initialization (Global) ---
try:
    if globals().get('__firebase_config'):
        firebase_config_str = globals()['__firebase_config']
        firebase_config = json.loads(firebase_config_str)
        print("Using Firebase config from Canvas environment.")
    else:
        local_credentials_path = 'firebase_credentials.json'
        if os.path.exists(local_credentials_path):
            with open(local_credentials_path, 'r') as f:
                firebase_config = json.load(f)
            print(f"Using local Firebase credentials from {local_credentials_path}.")
        else:
            st.error("Firebase credentials file 'firebase_credentials.json' not found. Please follow setup instructions.")
            raise FileNotFoundError("Local Firebase credentials file not found.")

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
    db = firestore.client()
    st.session_state['db'] = db
    st.session_state['firebase_initialized'] = True
    print("Firebase initialized successfully.")
except Exception as e:
    st.error(f"Failed to initialize Firebase: {e}")
    st.session_state['firebase_initialized'] = False
    print(f"Firebase initialization failed: {e}")

# --- Global Variables for Firestore Paths ---
if '__app_id' in globals():
    APP_ID = globals()['__app_id']
    print(f"Using APP_ID from Canvas: {APP_ID}")
else:
    APP_ID = 'local-axon-app-dev'
    print(f"Using default local APP_ID: {APP_ID}")

PUBLIC_DATA_PATH = f"artifacts/{APP_ID}/public/data"
PRIVATE_DATA_PATH = f"artifacts/{APP_ID}/users"

# --- Helper Functions for Database Operations ---
def get_user_id():
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = str(uuid.uuid4())
    return st.session_state['user_id']

def get_medicine_ref(medicine_name: str):
    if not st.session_state.get('firebase_initialized'):
        print("Firebase not initialized, cannot get medicine reference.")
        return None
    medicines_ref = st.session_state['db'].collection(f"{PUBLIC_DATA_PATH}/medicines")
    query = medicines_ref.where(filter=FieldFilter("name", "==", medicine_name.lower()))
    docs = query.get()
    if docs:
        return docs[0]
    return None

def check_medicine_availability(medicine_name: str) -> dict:
    if not st.session_state.get('firebase_initialized'):
        return {"medicine_name": medicine_name, "available": False, "message": "Database not available."}
    medicine_doc = get_medicine_ref(medicine_name)
    if medicine_doc:
        data = medicine_doc.to_dict()
        return {"medicine_name": data['name'], "stock": data['stock'], "available": data['stock'] > 0}
    return {"medicine_name": medicine_name, "stock": 0, "available": False, "message": f"Medicine '{medicine_name}' not found."}

def get_medicine_info(medicine_name: str) -> dict:
    if not st.session_state.get('firebase_initialized'):
        return {"medicine_name": medicine_name, "message": "Database not available."}
    medicine_doc = get_medicine_ref(medicine_name)
    if medicine_doc:
        data = medicine_doc.to_dict()
        return {
            "medicine_name": data['name'],
            "description": data.get('description', 'No description available.'),
            "side_effects": data.get('side_effects', 'No known side effects listed.'),
            "price": data.get('price', 'Price not available.')
        }
    return {"medicine_name": medicine_name, "message": f"Medicine '{medicine_name}' not found."}

def place_order(user_id: str, medicine_name: str, quantity: int) -> dict:
    if not st.session_state.get('firebase_initialized'):
        return {"success": False, "message": "Database not available."}
    medicine_doc = get_medicine_ref(medicine_name)
    if not medicine_doc:
        return {"success": False, "message": f"Medicine '{medicine_name}' not found."}
    medicine_data = medicine_doc.to_dict()
    if medicine_data['stock'] < quantity:
        return {"success": False, "message": f"Not enough stock for {medicine_name}. Available: {medicine_data['stock']}."}
    if quantity <= 0:
        return {"success": False, "message": "Quantity must be positive."}
    try:
        new_stock = medicine_data['stock'] - quantity
        medicine_doc.reference.update({"stock": new_stock})
        orders_ref = st.session_state['db'].collection(f"{PRIVATE_DATA_PATH}/{user_id}/orders")
        order_data = {
            "user_id": user_id,
            "medicine_id": medicine_doc.id,
            "medicine_name": medicine_data['name'],
            "quantity": quantity,
            "price_per_unit": medicine_data['price'],
            "total_price": medicine_data['price'] * quantity,
            "order_date": datetime.datetime.now(),
            "status": "pending"
        }
        orders_ref.add(order_data)
        return {"success": True, "message": f"Order for {quantity} units of {medicine_name} placed successfully. New stock: {new_stock}."}
    except Exception as e:
        return {"success": False, "message": f"Error placing order: {e}"}

def get_order_history(user_id: str) -> list:
    if not st.session_state.get('firebase_initialized'):
        return []
    orders_ref = st.session_state['db'].collection(f"{PRIVATE_DATA_PATH}/{user_id}/orders")
    orders = []
    try:
        docs = orders_ref.order_by("order_date", direction=firestore.Query.DESCENDING).limit(5).get()
        for doc in docs:
            order_data = doc.to_dict()
            orders.append({
                "order_id": doc.id,
                "medicine_name": order_data.get('medicine_name', 'N/A'),
                "quantity": order_data.get('quantity', 0),
                "total_price": order_data.get('total_price', 0),
                "status": order_data.get('status', 'N/A'),
                "order_date": order_data.get('order_date').strftime("%Y-%m-%d %H:%M:%S") if order_data.get('order_date') else 'N/A'
            })
    except Exception as e:
        print(f"Error fetching order history for user {user_id}: {e}")
    return orders

def log_chat_interaction(user_id: str, user_message: str, agent_response: str, functions_called: list) -> bool:
    if not st.session_state.get('firebase_initialized'):
        print("Firebase not initialized, cannot log chat interaction.")
        return False
    try:
        chat_logs_ref = st.session_state['db'].collection(f"{PRIVATE_DATA_PATH}/{user_id}/chat_logs")
        chat_logs_ref.add({
            "user_id": user_id,
            "timestamp": datetime.datetime.now(),
            "user_message": user_message,
            "agent_response": agent_response,
            "functions_called": functions_called
        })
        return True
    except Exception as e:
        print(f"Error logging chat interaction: {e}")
        return False

def send_telegram_notification(message: str) -> dict:
    # Use os.getenv to retrieve Telegram credentials from environment variables
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    channel_username = os.getenv('CHANNEL_USERNAME')
    group_username = os.getenv('GROUP_USERNAME')

    if not telegram_bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set.")
        return {"success": False, "message": "Telegram bot token not configured."}
    if not channel_username and not group_username:
        print("Error: Neither CHANNEL_USERNAME nor GROUP_USERNAME environment variables set.")
        return {"success": False, "message": "Telegram channel/group not configured."}

    # Simulate the Telegram API call
    print(f"--- SIMULATED TELEGRAM NOTIFICATION ---")
    print(f"Attempting to send message to Telegram Channel/Group:")
    print(f"Bot Token (simulated): {telegram_bot_token[:5]}...")
    print(f"Channel: {channel_username if channel_username else 'N/A'}")
    print(f"Group: {group_username if group_username else 'N/A'}")
    print(f"Message: {message}")
    print(f"---------------------------------------")

    # In a real application, you would make an HTTP request here:
    # import requests
    # url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
    # params = {'chat_id': channel_username, 'text': message, 'parse_mode': 'HTML'}
    # response = requests.post(url, data=params)
    # Handle response.json()

    return {"success": True, "message": f"Simulated Telegram notification sent: '{message}'"}

# --- Admin-specific Database Functions ---
def add_medicine(name: str, stock: int, price: float, description: str, side_effects: str) -> dict:
    if not st.session_state.get('firebase_initialized'):
        return {"success": False, "message": "Database not available."}
    try:
        medicines_ref = st.session_state['db'].collection(f"{PUBLIC_DATA_PATH}/medicines")
        existing_medicine = get_medicine_ref(name)
        if existing_medicine:
            return {"success": False, "message": f"Medicine '{name}' already exists. Use 'Update Stock' instead."}
        medicines_ref.add({
            "name": name.lower(),
            "stock": stock,
            "price": price,
            "description": description,
            "side_effects": side_effects
        })
        send_telegram_notification(f"📢 New medicine added to Axon Pharmacy: {name.capitalize()}! Stock: {stock}.")
        return {"success": True, "message": f"Medicine '{name}' added successfully."}
    except Exception as e:
        return {"success": False, "message": f"Error adding medicine: {e}"}

def update_medicine_stock(medicine_name: str, new_stock: int) -> dict:
    if not st.session_state.get('firebase_initialized'):
        return {"success": False, "message": "Database not available."}
    medicine_doc = get_medicine_ref(medicine_name)
    if not medicine_doc:
        return {"success": False, "message": f"Medicine '{medicine_name}' not found. Add it first."}
    try:
        old_stock = medicine_doc.to_dict().get('stock', 0)
        medicine_doc.reference.update({"stock": new_stock})
        if new_stock == 0:
            send_telegram_notification(f"⚠️ Stock Alert: {medicine_name.capitalize()} is now out of stock!")
        elif new_stock > old_stock:
            send_telegram_notification(f"✅ Stock Update: {medicine_name.capitalize()} stock increased to {new_stock}.")
        else:
            send_telegram_notification(f"🔄 Stock Update: {medicine_name.capitalize()} stock changed to {new_stock}.")
        return {"success": True, "message": f"Stock for '{medicine_name}' updated to {new_stock}."}
    except Exception as e:
        return {"success": False, "message": f"Error updating stock: {e}"}

# --- LLM Agent Setup (using google-genai) ---
if 'gemini_client' not in st.session_state:
    try:
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        if not gemini_api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Initialize client with explicit API key
        st.session_state['gemini_client'] = genai.Client(api_key=gemini_api_key)
        print("Gemini client initialized with API key.")

        function_declarations = [
            types.FunctionDeclaration(
                name="check_medicine_availability",
                description="Checks the current stock availability of a specific medicine.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"medicine_name": types.Schema(type=types.Type.STRING)},
                    required=["medicine_name"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_medicine_info",
                description="Retrieves detailed information about a medicine, including its description, side effects, and price.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"medicine_name": types.Schema(type=types.Type.STRING)},
                    required=["medicine_name"],
                ),
            ),
            types.FunctionDeclaration(
                name="place_order",
                description="Places an order for a specified quantity of a medicine for a user. This also updates the medicine stock.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "user_id": types.Schema(type=types.Type.STRING, description="The unique ID of the user placing the order."),
                        "medicine_name": types.Schema(type=types.Type.STRING, description="The name of the medicine to order."),
                        "quantity": types.Schema(type=types.Type.NUMBER, description="The quantity of the medicine to order (must be a positive integer)."),
                    },
                    required=["user_id", "medicine_name", "quantity"],
                ),
            ),
            types.FunctionDeclaration(
                name="get_order_history",
                description="Retrieves the recent order history for a given user.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"user_id": types.Schema(type=types.Type.STRING, description="The unique ID of the user whose order history is requested.")},
                    required=["user_id"],
                ),
            ),
            types.FunctionDeclaration(
                name="log_chat_interaction",
                description="Logs a chat interaction between the user and the agent to the database, including the user's message, agent's response, and any functions called.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={
                        "user_id": types.Schema(type=types.Type.STRING, description="The unique ID of the user."),
                        "user_message": types.Schema(type=types.Type.STRING, description="The message sent by the user."),
                        "agent_response": types.Schema(type=types.Type.STRING, description="The response generated by the agent."),
                        "functions_called": types.Schema(type=types.Type.ARRAY, items=types.Schema(type=types.Type.STRING), description="A list of names of functions called during this interaction."),
                    },
                    required=["user_id", "user_message", "agent_response", "functions_called"],
                ),
            ),
            types.FunctionDeclaration(
                name="send_telegram_notification",
                description="Sends a simulated notification message to a Telegram channel or group. This is used for automated alerts like stock updates.",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties={"message": types.Schema(type=types.Type.STRING, description="The message content for the Telegram notification.")},
                    required=["message"],
                ),
            ),
        ]

        st.session_state['gemini_tools'] = types.Tool(function_declarations=function_declarations)
        st.session_state['gemini_config'] = types.GenerateContentConfig(
            tools=[st.session_state['gemini_tools']],
            # Optional: Add thinking configuration if needed
            thinking_config=types.ThinkingConfig(thinking_budget=1)
        )
        print("Gemini tools and configuration prepared.")

    except Exception as e:
        st.error(f"Failed to initialize Gemini client. Error: {e}")
        st.session_state['gemini_client'] = None
        st.session_state['gemini_tools'] = None
        st.session_state['gemini_config'] = None
        print(f"Gemini client initialization failed: {e}")

# --- Streamlit App Layout ---
st.set_page_config(page_title="Axon Pharmacy Agent", layout="wide")

query_params = st.query_params
current_role = query_params.get("role", ["user"])[0].lower()

st.sidebar.title("Navigation")
if st.sidebar.button("User Interface 🧑‍🔬"):
    st.query_params["role"] = "user"
    st.rerun()
if st.sidebar.button("Admin Interface ⚙️"):
    st.query_params["role"] = "admin"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write(f"**Current Role:** {current_role.capitalize()}")

if current_role == "user":
    st.sidebar.header("Your Session ID")
    st.sidebar.info(f"ID: {get_user_id()}")
    st.sidebar.caption("This ID is used to store your private data (orders, chat logs) for this session.")


# --- User Interface ---
def user_interface():
    st.title("💊 Axon Pharmacy Customer Service Agent")
    st.markdown("Hello! I'm your automated pharmacy assistant. How can I help you today?")

    user_id = get_user_id()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "function_calls" in message and message["function_calls"]:
                st.info(f"Functions called: {', '.join(message['function_calls'])}")

    if prompt := st.chat_input("Ask me about medicines, orders, or anything else!"):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt, "parts": [types.Part(text=prompt)]})
        with st.chat_message("user"):
            st.markdown(prompt)

        if not st.session_state.get('firebase_initialized') or not st.session_state.get('gemini_client'):
            with st.chat_message("assistant"):
                st.warning("System not fully initialized. Please wait or refresh.")
            return

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Build the full conversation history for the LLM
                    conversation_parts = []
                    for msg in st.session_state.messages:
                        conversation_parts.extend(msg["parts"])

                    # First call to LLM with user prompt and tools
                    response = st.session_state['gemini_client'].models.generate_content(
                        model="gemini-2.5-flash",
                        contents=conversation_parts, # Send entire history
                        config=st.session_state['gemini_config'],
                    )

                    function_calls_made = []
                    final_response_text = ""
                    model_response_parts_for_history = []

                    # Check if candidates exist and have content
                    if response.candidates and response.candidates[0].content:
                        for part in response.candidates[0].content.parts:
                            if part.function_call:
                                function_name = part.function_call.name
                                args = {k: v for k, v in part.function_call.args.items()}
                                st.info(f"LLM wants to call: `{function_name}` with args: `{args}`")
                                function_calls_made.append(function_name)

                                # Execute the function
                                result = {}
                                if function_name == "check_medicine_availability":
                                    result = check_medicine_availability(**args)
                                elif function_name == "get_medicine_info":
                                    result = get_medicine_info(**args)
                                elif function_name == "place_order":
                                    result = place_order(user_id=user_id, **args)
                                elif function_name == "get_order_history":
                                    result = get_order_history(user_id=user_id)
                                elif function_name == "log_chat_interaction":
                                    result = {"status": "deferred_logging"} # Handled after final response
                                elif function_name == "send_telegram_notification":
                                    result = send_telegram_notification(**args)
                                else:
                                    result = {"error": f"Unknown function: {function_name}"}

                                st.json(result) # Show the raw result from the function call

                                # Add the function call and its response to the parts for the next LLM turn
                                model_response_parts_for_history.append(part) # Add the function_call part
                                model_response_parts_for_history.append(types.Part(function_response=types.FunctionResponse(name=function_name, response=result)))

                            elif part.text:
                                final_response_text += part.text
                                model_response_parts_for_history.append(part) # Add the text part

                    # If function calls were made, we need to make another LLM call with the tool output
                    if function_calls_made:
                        # Append the model's function call(s) and tool output(s) to the session history
                        # The content for display can be a placeholder while functions are executing.
                        st.session_state.messages.append({"role": "assistant", "content": "Executing functions...", "parts": model_response_parts_for_history, "function_calls": function_calls_made})

                        # Re-build conversation parts with new tool outputs for the second LLM call
                        conversation_parts_with_tools = []
                        for msg in st.session_state.messages:
                            conversation_parts_with_tools.extend(msg["parts"])

                        # Second call to LLM to get the final text response after tool execution
                        final_response_llm = st.session_state['gemini_client'].models.generate_content(
                            model="gemini-2.5-flash",
                            contents=conversation_parts_with_tools, # Send history including tool outputs
                            config=st.session_state['gemini_config'],
                        )

                        # Extract final text response
                        if final_response_llm.candidates and final_response_llm.candidates[0].content and final_response_llm.candidates[0].content.parts:
                            final_response_text = final_response_llm.candidates[0].content.parts[0].text
                        else:
                            final_response_text = "The model did not provide a final text response after function execution."
                            print(f"Warning: No final text response from LLM after function calls. Full response: {final_response_llm}")

                        # Update the last assistant message in session state with the actual final text
                        # This is a bit tricky with Streamlit's session state and how we're building history.
                        # A simpler way might be to just append the final response.
                        st.session_state.messages[-1]["content"] = final_response_text
                        st.session_state.messages[-1]["parts"].append(types.Part(text=final_response_text)) # Add final text part to history

                    else:
                        # If no function calls, the initial text response is the final one
                        # Ensure final_response_text is set from the initial response if no functions were called
                        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                            final_response_text = response.candidates[0].content.parts[0].text
                        else:
                            final_response_text = "The model did not provide a text response."
                            print(f"Warning: No text response from LLM in initial call. Full response: {response}")

                        st.session_state.messages.append({"role": "assistant", "content": final_response_text, "parts": model_response_parts_for_history})


                    st.markdown(final_response_text)

                    # Log the interaction after the full exchange
                    log_chat_interaction(user_id, prompt, final_response_text, function_calls_made)

                except Exception as e:
                    error_message = f"An error occurred during LLM interaction: {e}"
                    st.error(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": f"Sorry, I encountered an error: {e}", "parts": [types.Part(text=f"Sorry, I encountered an error: {e}")]})
                    print(f"Detailed LLM interaction error: {e}")

# --- Admin Interface ---
def admin_interface():
    st.title("⚙️ Axon Pharmacy Admin Panel")
    st.markdown("Manage medicines, view logs, and send notifications.")

    if not st.session_state.get('firebase_initialized'):
        st.warning("Firebase not initialized. Admin functions are disabled.")
        return

    st.header("Manage Medicines")
    with st.form("medicine_form"):
        st.subheader("Add New Medicine / Update Stock")
        med_name = st.text_input("Medicine Name (e.g., Paracetamol)", key="admin_med_name").strip().lower()
        med_stock = st.number_input("Stock Quantity", min_value=0, value=100, step=1, key="admin_med_stock")
        med_price = st.number_input("Price", min_value=0.0, value=10.50, step=0.1, format="%.2f", key="admin_med_price")
        med_desc = st.text_area("Description", key="admin_med_desc", value="A common pain reliever.")
        med_side_effects = st.text_area("Side Effects", key="admin_med_side_effects", value="Mild nausea, stomach upset.")

        col1, col2 = st.columns(2)
        with col1:
            add_submit = st.form_submit_button("Add New Medicine")
        with col2:
            update_submit = st.form_submit_button("Update Existing Medicine Stock")

        if add_submit:
            if med_name:
                result = add_medicine(med_name, med_stock, med_price, med_desc, med_side_effects)
                if result['success']:
                    st.success(result['message'])
                else:
                    st.error(result['message'])
            else:
                st.warning("Medicine Name is required to add.")
        elif update_submit:
            if med_name:
                result = update_medicine_stock(med_name, med_stock)
                if result['success']:
                    st.success(result['message'])
                else:
                    st.error(result['message'])
            else:
                st.warning("Medicine Name is required to update stock.")

    st.markdown("---")

    st.header("Current Medicine Inventory")
    medicines_ref = st.session_state['db'].collection(f"{PUBLIC_DATA_PATH}/medicines")
    try:
        all_medicines = medicines_ref.get()
        medicine_data = []
        for doc in all_medicines:
            data = doc.to_dict()
            medicine_data.append({
                "Name": data.get('name').capitalize() if data.get('name') else 'N/A',
                "Stock": data.get('stock'),
                "Price": data.get('price'),
                "Description": data.get('description', 'N/A'),
                "Side Effects": data.get('side_effects', 'N/A')
            })
        if medicine_data:
            st.dataframe(medicine_data, use_container_width=True)
        else:
            st.info("No medicines in inventory yet. Use the form above to add some!")
    except Exception as e:
        st.error(f"Error fetching medicines: {e}")

    st.markdown("---")

    st.header("Customer Chat Logs")
    st.markdown("Displays recent chat interactions across all users.")
    chat_logs_query = st.session_state['db'].collection_group("chat_logs") \
                                            .order_by("timestamp", direction=firestore.Query.DESCENDING) \
                                            .limit(20)

    try:
        docs = chat_logs_query.get()
        logs = []
        for doc in docs:
            log_data = doc.to_dict()
            logs.append({
                "User ID": log_data.get('user_id'),
                "Timestamp": log_data.get('timestamp').strftime("%Y-%m-%d %H:%M:%S") if log_data.get('timestamp') else 'N/A',
                "User Message": log_data.get('user_message'),
                "Agent Response": log_data.get('agent_response'),
                "Functions Called": ", ".join(log_data.get('functions_called', []))
            })
        if logs:
            st.dataframe(logs, use_container_width=True)
        else:
            st.info("No chat logs available yet.")
    except Exception as e:
        st.error(f"Error fetching chat logs: {e}")

    st.markdown("---")

    st.header("Send Manual Telegram Notification (Simulated)")
    telegram_message = st.text_area("Message to send to Telegram:", key="telegram_msg", value="Important update from Axon Pharmacy!")
    if st.button("Send Simulated Telegram Notification Manually"):
        if telegram_message:
            result = send_telegram_notification(telegram_message)
            if result['success']:
                st.success(result['message'])
            else:
                st.error(result['message'])
        else:
            st.warning("Please enter a message to send.")


# --- Main App Logic (Routing) ---
if current_role == "admin":
    admin_interface()
else:
    user_interface()
