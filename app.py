# app.py

import os
import uuid
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import hashlib
from typing import Optional, List, Dict, Any
import json

from function_declarations import (
    check_availability_function,
    place_order_function,
    track_order_function,
    cancel_order_function,
    get_health_advice_function
)


load_dotenv()

# Initialize Firebase
if not firebase_admin._apps:
    try:
        cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Failed to initialize Firebase: {str(e)}")
        st.stop()

db = firestore.client()

client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

st.set_page_config(
    page_title="Axon Pharmacy",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
    }


    .function-call {
        background-color: #fff8e1;
        padding: 8px;
        border-radius: 5px;
        margin: 5px 0;
        font-family: monospace;
    }
</style>
""", unsafe_allow_html=True)

# Authentication Functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    try:
        user_ref = db.collection("users").document(email)
        user_data = user_ref.get()
        
        if user_data.exists:
            hashed_password = hash_password(password)
            stored_password = user_data.to_dict().get("password")
            
            if hashed_password == stored_password:
                return {
                    "success": True,
                    "user_data": user_data.to_dict(),
                    "message": "Authentication successful"
                }
        
        return {
            "success": False,
            "message": "Invalid email or password"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }

def register_user(email: str, password: str, name: str, age: int) -> Dict[str, Any]:
    user_ref = db.collection("users").document(email)
    if user_ref.get().exists:
        return {
            "success": False,
            "message": "User already exists"
        }
    user_data = {
        "email": email,
        "password": hash_password(password),
        "name": name,
        "age": age,
        "created_at": datetime.now(),
        "orders": {},
        "chat_history": []
    }
    user_ref.set(user_data)
    return {
        "success": True,
        "message": "Registration successful"
    }

def check_medicine_availability(medicine_name: str) -> Dict[str, Any]:
    medicine_name = medicine_name.lower().replace(' ', '_')
    medicine_ref = db.collection("medicines").document(medicine_name)
    medicine_data = medicine_ref.get()
    
    if not medicine_data.exists:
        return {
            "success": False,
            "message": f"Medicine '{medicine_name}' not found"
        }
    
    medicine_dict = medicine_data.to_dict()
    return {
        "success": True,
        "data": {
            "name": medicine_dict.get("name"),
            "stock": medicine_dict.get("stock", 0),
            "unit_price": medicine_dict.get("unit_price", 0),
            "description": medicine_dict.get("description", ""),
            "category": medicine_dict.get("category", "General")
        }
    }

def place_order(medicine_name: str, quantity: int, user_email: str) -> Dict[str, Any]:
    # Check medicine availability
    availability = check_medicine_availability(medicine_name)
    if not availability["success"]:
        return availability
    
    medicine_data = availability["data"]
    if medicine_data["stock"] < quantity:
        return {
            "success": False,
            "message": f"Not enough stock. Available: {medicine_data['stock']}"
        }
    # generate order id
    order_id = str(uuid.uuid4())

    total_price = quantity * medicine_data["unit_price"]
    
    # Create order document
    order_data = {
        "order_id": order_id,
        "user_email": user_email,
        "medicine_name": medicine_name,
        "quantity": quantity,
        "unit_price": medicine_data["unit_price"],
        "total_price": total_price,
        "status": "pending",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    # Update medicine stock
    new_stock = medicine_data["stock"] - quantity
    name = medicine_name.lower().replace(' ', '_')
    db.collection("medicines").document(name).update({
        "stock": new_stock
    })
    
    # record it
    db.collection("orders").document(order_id).set(order_data)
    
    # Add order reference to users document
    user_ref = db.collection("users").document(user_email)
    user_ref.update({
        f"orders.{order_id}": medicine_name
    })
    
    return {
        "success": True,
        "order_id": order_id,
        "data": order_data,
        "message": f"Order placed successfully! Order ID: {order_id}"
    }

def track_order(order_id: str, user_email: str) -> Dict[str, Any]:
    try:
        order_ref = db.collection("orders").document(order_id)
        order_data = order_ref.get()
        
        if not order_data.exists:
            return {
                "success": False,
                "message": "Order not found"
            }
        
        order_dict = order_data.to_dict()
        
        # Verify order belongs to user
        if order_dict["user_email"] != user_email:
            return {
                "success": False,
                "message": "This order doesn't belong to you"
            }
        
        return {
            "success": True,
            "data": order_dict,
            "message": f"Order status for ID {order_id}: **{order_dict.get('status', 'unknown').upper()}**"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error tracking order: {str(e)}"
        }

def cancel_order(order_id: str, user_email: str) -> Dict[str, Any]:
    try:
        # First verify the order exists and belongs to user
        track_result = track_order(order_id, user_email)
        if not track_result["success"]:
            return track_result
        
        order_data = track_result["data"]
        
        if order_data["status"].lower() not in ["pending", "processing"]:
            return {
                "success": False,
                "message": f"Cannot cancel order with status: {order_data['status']}. Please contact support for assistance."
            }
        
        # Update order status
        db.collection("orders").document(order_id).update({
            "status": "cancelled",
            "updated_at": datetime.now()
        })
        
        # restore medicine stock
        medicine_name = order_data["medicine_name"]
        quantity = order_data["quantity"]
        
        medicine_ref = db.collection("medicines").document(medicine_name.lower().replace(' ', '_'))
        medicine_ref.update({
            "stock": firestore.Increment(quantity)
        })
        
        return {
            "success": True,
            "message": f"Order {order_id} cancelled successfully."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error cancelling order: {str(e)}"
        }

def get_health_advice(user_email: str, symptoms: Optional[str] = None) -> Dict[str, Any]:
    try:
        # Get user data
        user_ref = db.collection("users").document(user_email)
        user_data = user_ref.get().to_dict()
        
        if not user_data:
            return {
                "success": False,
                "message": "User data not found"
            }
        
        # Get user's order history
        orders = user_data.get("orders", {})
        
        # Fetch details for ordered medicines if available
        order_details = {}
        for order_id, med_name in orders.items():
            med_info = check_medicine_availability(med_name)
            if med_info["success"]:
                order_details[order_id] = med_info["data"]
            else:
                order_details[order_id] = {"name": med_name, "status": "details unavailable"}

        # Prepare context for health advice
        context = {
            "user": {
                "name": user_data.get("name"),
                "age": user_data.get("age"),
                "email": user_email,
                "order_history_summary": [{"order_id": oid, "medicine": details.get("name"), "description": details.get("description")} for oid, details in order_details.items()]
            },
            "symptoms": symptoms if symptoms else "No specific symptoms provided, giving general advice."
        }
        
        return {
            "success": True,
            "data": context,
            "message": "Context collected for health advice."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting health advice: {str(e)}"
        }


# Initialize Gemini Tools
def initialize_gemini_tools():
    tools = types.Tool(function_declarations=[
        check_availability_function,
        place_order_function,
        track_order_function,
        cancel_order_function,
        get_health_advice_function
    ])
    
    config = types.GenerateContentConfig(
        tools=[tools],
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode="AUTO")
        )
    )
    
    return config

# UI Components
def display_chat_message(role: str, content: str, function_calls: List[str] = None, function_results: List[Dict] = None):
    with st.chat_message(role):
        # Display message content
        st.markdown(f'<div class="chat-message {role}-message">{content}</div>', unsafe_allow_html=True)
        
        # Display function calls if any
        if function_calls:
            with st.expander("Function Calls"):
                for call in function_calls:
                    st.code(call, language="python")
        
        # Display function results if any
        if function_results:
            with st.expander("Action Details"):
                for result in function_results:
                    if result.get("success"):
                        st.success(result.get("message", "Action completed"))
                        if "data" in result and result["data"]: # Check if 'data' exists and is not empty
                            st.json(result["data"])
                    else:
                        st.error(result.get("message", "Action failed"))

def login_page():
    st.title("Axon Pharmacy Login")
    st.markdown("---")
    
    with st.form("login_form"):
        email = st.text_input("Email", key="login_email").strip().lower()
        password = st.text_input("Password", type="password", key="login_password")
        login_button = st.form_submit_button("Login")
        
        if login_button:
            if not email or not password:
                st.warning("Please enter both email and password")
                return
            
            auth_result = authenticate_user(email, password)
            if auth_result["success"]:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.user_data = auth_result["user_data"]
                st.session_state.messages = [] 
                
                # Initialize Gemini chat with conversation history
                try:
                    st.session_state.gemini_config = initialize_gemini_tools()
                    st.session_state.gemini_chat = client.chats.create(
                        model="gemini-2.5-flash",
                        config=st.session_state.gemini_config
                    )
                    # Load chat history from Firestore
                    if "chat_history" in st.session_state.user_data and st.session_state.user_data["chat_history"]:
                        for history_entry in st.session_state.user_data["chat_history"]:
                            if history_entry.get("role") == "user":
                                st.session_state.gemini_chat.send_message(history_entry.get("content"))
                                st.session_state.messages.append({"role": "user", "content": history_entry.get("content")})
                            elif history_entry.get("role") == "model":
                                # Assuming model responses in history are text only for simplicity, adjust if they contained tool outputs
                                st.session_state.messages.append({"role": "assistant", "content": history_entry.get("content")})
                    
                except Exception as e:
                    st.error(f"Failed to initialize chat: {str(e)}")
                    st.session_state.logged_in = False
                    return
                
                st.rerun()
            else:
                st.error(auth_result["message"])

    st.markdown("---")
    st.markdown("Don't have an account?")
    if st.button("Register Now"):
        st.session_state.current_page = "register"
        st.rerun()

def register_page():
    st.title("Axon Pharmacy Registration")
    st.markdown("---")
    
    with st.form("register_form"):
        name = st.text_input("Full Name", key="reg_name").strip()
        email = st.text_input("Email", key="reg_email").strip().lower()
        password = st.text_input("Password", type="password", key="reg_password")
        age = st.number_input("Age", min_value=1, max_value=120, value=25, key="reg_age")
        register_button = st.form_submit_button("Register")
        
        if register_button:
            if not all([name, email, password, age]):
                st.warning("Please fill all required fields")
                return
            
            if "@" not in email and "." not in email:
                st.warning("Please enter a valid email address")
                return
            
            reg_result = register_user(email, password, name, age)
            if reg_result["success"]:
                st.success(reg_result["message"] + " Please login now.")
                st.session_state.current_page = "login"
                st.rerun()
            else:
                st.error(reg_result["message"])

    st.markdown("---")
    if st.button("Back to Login"):
        st.session_state.current_page = "login"
        st.rerun()

def chat_page():
    st.title(f"Welcome, {st.session_state.user_data.get('name', 'User')}!")
    st.caption("How can I help you with your pharmacy needs today?")
    st.markdown("---")
    
    # Display chat history
    for message in st.session_state.messages:
        display_chat_message(
            role=message["role"],
            content=message["content"],
            function_calls=message.get("function_calls"),
            function_results=message.get("function_results")
        )
    
    # User input
    if prompt := st.chat_input("Ask about medicines, place orders, or get health advice..."):
        # Add user message to chat history (local session state)
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Display user message
        display_chat_message("user", prompt)
        
        # Prepare contents for the current turn, starting with user's prompt
        current_turn_contents = [
            types.Content(role="user", parts=[types.Part(text=prompt)])
        ]

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Send message to Gemini for this turn
                    # We send only the current user prompt initially.
                    # If function calls occur, we'll build up `current_turn_contents`
                    # and make a final call to client.models.generate_content.
                    # Otherwise, the response.text is the final answer.
                    response = st.session_state.gemini_chat.send_message(prompt)
                    
                    function_calls_display = []
                    function_results_display = []
                    assistant_response_text = ""
                    
                    # If the model suggests function calls
                    if response.function_calls:
                        # Append the model's function call part to the conversation history
                        current_turn_contents.append(response.candidates[0].content)

                        for fn_call in response.function_calls:
                            fn_name = fn_call.name
                            fn_args = fn_call.args
                            
                            # Log function call for display
                            function_calls_display.append(f"{fn_name}({json.dumps(fn_args, indent=2)})")
                            
                            # Call the appropriate function
                            result = None
                            try:
                                if fn_name == "check_medicine_availability":
                                    result = check_medicine_availability(fn_args["medicine_name"])
                                elif fn_name == "place_order":
                                    result = place_order(
                                        fn_args["medicine_name"],
                                        fn_args["quantity"],
                                        st.session_state.user_email
                                    )
                                elif fn_name == "track_order":
                                    result = track_order(
                                        fn_args["order_id"],
                                        st.session_state.user_email
                                    )
                                elif fn_name == "cancel_order":
                                    result = cancel_order(
                                        fn_args["order_id"],
                                        st.session_state.user_email
                                    )
                                elif fn_name == "get_health_advice":
                                    # Handle optional symptoms parameter
                                    symptoms_arg = fn_args.get("symptoms") if "symptoms" in fn_args else None
                                    result = get_health_advice(
                                        st.session_state.user_email,
                                        symptoms_arg
                                    )
                                
                                function_results_display.append(result)
                                
                                # Append function response to contents for Gemini
                                current_turn_contents.append(
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_function_response(
                                            name=fn_name,
                                            response={"result": result} # Ensure result is a dictionary
                                        )]
                                    )
                                )
                                
                            except Exception as e:
                                error_res = {
                                    "success": False,
                                    "message": f"Error executing {fn_name}: {str(e)}"
                                }
                                function_results_display.append(error_res)
                                current_turn_contents.append(
                                    types.Content(
                                        role="user",
                                        parts=[types.Part.from_function_response(
                                            name=fn_name,
                                            response={"result": error_res}
                                        )]
                                    )
                                )
                        
                        # After executing all functions, send the full turn history back to Gemini
                        final_model_response = client.models.generate_content(
                            model="gemini-2.5-flash",
                            config=st.session_state.gemini_config,
                            contents=current_turn_contents,
                        )
                        assistant_response_text = final_model_response.text
                    else:
                        # If no function calls, the initial response text is the final answer
                        assistant_response_text = response.text
                    
                    # Add assistant response to chat history (local session state)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response_text,
                        "function_calls": function_calls_display,
                        "function_results": function_results_display
                    })

                    # Save chat history to Firestore (append current turn)
                    user_doc_ref = db.collection("users").document(st.session_state.user_email)
                    user_doc_ref.update({
                        "chat_history": firestore.ArrayUnion([
                            {"role": "user", "content": prompt},
                            {"role": "model", "content": assistant_response_text, "function_calls": function_calls_display, "function_results": function_results_display}
                        ])
                    })

                    # Display assistant response
                    display_chat_message(
                        "assistant",
                        assistant_response_text,
                        function_calls_display,
                        function_results_display
                    )
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg
                    })
    
    # Sidebar with user info and quick actions
    with st.sidebar:
        st.title("Your Account")
        st.markdown(f"**Name:** {st.session_state.user_data.get('name', 'N/A')}")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown(f"**Age:** {st.session_state.user_data.get('age', 'N/A')}")
        
        st.markdown("---")
        st.title("Quick Actions")
        
        # Display user's current orders for easy tracking/cancellation
        st.subheader("Your Orders")
        user_orders = st.session_state.user_data.get("orders", {})
        if user_orders:
            for order_id, medicine_name in user_orders.items():
                st.write(f"- **{medicine_name.replace('_', ' ').title()}** (ID: `{order_id[:8]}...`)") # Show truncated ID
        else:
            st.info("You don't have any active orders.")

        st.markdown("---") # Separator for quick action forms

        with st.expander("Track Order"):
            order_id_track = st.text_input("Enter Order ID to Track", key="order_status_id")
            if st.button("Track Order", key="track_btn") and order_id_track:
                result = track_order(order_id_track, st.session_state.user_email)
                if result["success"]:
                    st.success(result["message"])
                    st.json(result["data"])
                else:
                    st.error(result["message"])
        
        with st.expander("Cancel Order"):
            order_id_cancel = st.text_input("Enter Order ID to Cancel", key="order_cancel_id")
            if st.button("Cancel Order", key="cancel_btn") and order_id_cancel:
                result = cancel_order(order_id_cancel, st.session_state.user_email)
                if result["success"]:
                    st.success(result["message"])
                    # Refresh user data to reflect cancelled order
                    st.session_state.user_data = db.collection("users").document(st.session_state.user_email).get().to_dict()
                else:
                    st.error(result["message"])

        # Health Advice button moved out of expander for direct access if preferred
        if st.button("Get Health Advice"):
            # A simple prompt can trigger the tool or you can ask for symptoms
            st.session_state.messages.append({"role": "user", "content": "I need some general health advice."})
            display_chat_message("user", "I need some general health advice.")
            # This will trigger the get_health_advice tool via the main chat logic
            st.rerun() # Rerun to process the new user message

        st.markdown("---")
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()

# Main App
def main():
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "login"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    
    # Page routing
    if not st.session_state.logged_in:
        if st.session_state.current_page == "login":
            login_page()
        elif st.session_state.current_page == "register":
            register_page()
    else:
        chat_page()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center;">
        <p>📱 Join our <a href="https://t.me/axon_pharmacy" target="_blank">Telegram channel</a> for updates</p>
        <p>🌐 Visit our <a href="https://axonpharma.com" target="_blank">website</a></p>
        <p>📞 Contact us: +251111234567</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

