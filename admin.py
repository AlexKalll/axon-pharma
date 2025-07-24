import os
import requests
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import hashlib
from typing import Optional, List, Dict

from function_declarations import telegram_post_function, add_medicine_function, stock_out_function, add_stock_function, delete_medicine_function, update_order_status_function

from firebase.db_manager import db

load_dotenv()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

st.set_page_config(
    page_title="Axon Pharmacy Admin",
    page_icon="💊",
    layout="wide"
)

st.markdown("""
<style>
    .stButton>button {width: 100%;}
</style>
""", unsafe_allow_html=True)

# Authentication
def authenticate_admin(email: str, password: str) -> bool:
    try:
        if not email or not password: 
            return False
            
        admin_ref = db.collection("admins").document(email)
        admin_data = admin_ref.get()
        
        if admin_data.exists:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            stored_password = admin_data.to_dict().get("password")
            if hashed_password == stored_password:
                return True
        return False
    except Exception as e:
        st.error(f"Authentication error: {e}")
        return False

# Telegram Function
def telegram_post(message: str) -> dict:
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    targets = {
        'channel': os.getenv('CHANNEL_USERNAME'),
        'group': os.getenv('GROUP_USERNAME')
    }
    results = {}
    
    for name, target in targets.items():
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                data={
                    'chat_id': target,
                    'text': message,
                    'parse_mode': 'HTML',
                })
            
            response = response.json()
            results[name] = {
                'success': response.get('ok'),
                'message': response.get('result').get('text')
            }
        except Exception as e:
            results[name] = {
                'success': False,
                'error': str(e)
            }
    return results

def add_medicine(name: str, unit_price: float = 15, stock: int = 100, madein: str = "USA", category: str = "General", description: str = "For quality health") -> dict:
    try:
        name = name.lower().replace(' ', '_')
        doc_ref = db.collection("medicines").document(name)

        if doc_ref.get().exists:
            return {"success": False, "error": f"The {name} medicine already exists. instead you can update its stock."}
        
        data = {
            "name": name,
            "unit_price": unit_price,
            "stock": stock,
            "madein": madein,
            "category": category,
            "description": description,
            "created_at": datetime.now(),
        }
        doc_ref.set(data)
        return {"success": True, "message": f"The {name} medicine recorded successfully with the following details: Name: {name}, Unit Price: {unit_price}, Stock: {stock}, Madein: {madein}, Category: {category}, Description: {description}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def stock_out(name: str) -> dict:
    try:
        name = name.lower().replace(' ', '_')
        docs = db.collection("medicines").document(name)
        if docs:
            docs.update({ "stock": 0})

            return {"success": True, 'message': f"{name} medicine is now out of stock"}
        
        return {"success": False, "error": "Medicine not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_stock(name: str, quantity: int) -> dict:
    try:
        name = name.lower().replace(' ', '_')
        docs = db.collection("medicines").document(name)
        if docs.get().exists == True:
            docs.update({ "stock": docs.get().to_dict().get('stock') + quantity})

            return {"success": True, 'message': f"{name} medicine stock has been updated, increased by {quantity}"}
        
        return {"success": False, "error": f"{name} Medicine is not found, please add the medicine first."}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def delete_medicine(name: str) -> dict:
    try:
        name = name.lower().replace(' ', '_')
        docs = db.collection("medicines").document(name)
        if docs:
            docs.delete()
            return {"success": True, 'message': f"{name} medicine has been deleted"}
        
        return {"success": False, "error": "Medicine not found"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_order_status(order_id: str, status: str) -> dict[str, str]:
    try:
        doc_ref = db.collection("orders").document(order_id)
        doc_ref.update({
            "status": status,
            "updated_at": datetime.now()
        })
        return {"success": True, "message": f"Order {order_id} status updated to {status}."}
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Initialize chat session
if "messages" not in st.session_state:
    st.session_state.messages = []

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    with st.sidebar:
        st.title("Admin Login")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        
        if st.button("Login"):
            if authenticate_admin(email, password):
                st.session_state.logged_in = True
                st.session_state.admin = email
                st.rerun()
            else:
                st.error("Invalid credentials")
    st.stop()

# app
with st.sidebar:
    st.title(f"Welcome, Admin")
    st.caption(f"{st.session_state.admin}")
    st.markdown("---")
    st.info("Settings:")
    if st.button("Refresh"):
        st.session_state.messages = []
        st.rerun()
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.title("What can I do for you?")
    st.markdown("""
                - Automatic telegram post
                - Add a new medicine 
                - Stock out a medicine
                - Add stock to a medicine
                - Delete a medicine
                - Update order status
               """)
    st.markdown("---")
    st.info("Quick Infos:")
    st.code(f"Medicines in DB: {len(db.collection('medicines').get())}")
    st.code(f"Pending orders: {len(db.collection('orders').where('status', '==', 'pending').get())}")

# ui
st.title("Axon Pharmacy Service Automation with LLM")
st.caption("Chat with the admin assistant to manage your pharmacy")

for message in st.session_state.messages:  
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("🧑"):
        st.markdown(prompt)

    contents = [ types.Content(role="user", parts=[types.Part(text=prompt)]) ]

    # generate response
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            try:
                #  tools
                tools = types.Tool(function_declarations=[
                    telegram_post_function,
                    add_medicine_function,
                    stock_out_function, add_stock_function,
                    delete_medicine_function,
                    update_order_status_function
                ])
                config = types.GenerateContentConfig(
                    tools=[tools],
                    tool_config=types.ToolConfig(
                        function_calling_config=types.FunctionCallingConfig(mode="AUTO")
                    )
                )
                
                chat = client.chats.create(model = "gemini-2.5-flash", config=config)
                response = chat.send_message(prompt)


                i = 0
                functions_called = []
                for fn in response.function_calls:
                    i += 1
                    st.info(f"{i}. Excuting: {fn.name}() function")
                    functions_called.append(fn.name)
                    
                    tool_call = response.candidates[0].content.parts[i-1].function_call
                    if tool_call.name == "telegram_post":
                        result = telegram_post(**tool_call.args)
                    elif tool_call.name == "add_medicine":
                        result = add_medicine(**tool_call.args)
                    elif tool_call.name == "stock_out":
                        result = stock_out(**tool_call.args)
                    elif tool_call.name == "add_stock":
                        result = add_stock(**tool_call.args)
                    elif tool_call.name == "delete_medicine":
                        result = delete_medicine(**tool_call.args)
                    elif tool_call.name == "update_order_status":
                        result = update_order_status(**tool_call.args)

                    # Create a function response part
                    function_response_part = types.Part.from_function_response(
                        name=fn.name,
                        response={"result": result},
                    )

                    contents.append(response.candidates[0].content)
                    contents.append(types.Content(role="user", parts=[function_response_part]))

                final_response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    config=config,
                    contents=contents,
                )

                st.session_state.messages.append({"role": "model", "content": final_response.text})

                if len(functions_called) == 1:
                    st.info(f"Function executed: {', '.join(functions_called)}")
                if len(functions_called) > 1:
                    st.info(f"Functions executed are: {', '.join(functions_called)}")
                   
                st.markdown(final_response.text)
                    
            except Exception as e:
                st.warning("No response from AI, please try again later with quality prompts.")
                