import os
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv
from firebase_admin import firestore
from datetime import datetime
import hashlib
from typing import Dict, Any

from function_declarations import (
    check_availability_function,
    place_order_function,
    track_order_function,
    cancel_order_function,
    get_health_advice_function)

from scripts.user_functions import (
    check_medicine_availability,
    place_order,
    track_order,
    cancel_order,
    get_health_advice)
from firebase.db_manager import db

load_dotenv()

client = genai.Client()
st.set_page_config(
    page_title="Axon Pharmacy",
    page_icon="💊",
    layout="centered",
    initial_sidebar_state="expanded"
)
# CSS for better UI of buttons
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: bold;
        color: white;
        background-color: gray;
    }
</style>
""", unsafe_allow_html=True)

def authenticate_user(email: str, password: str) -> Dict[str, Any]:
    try:
        user_ref = db.collection("users").document(email)
        user_data = user_ref.get()
        
        if user_data.exists:
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
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
        "password": hashlib.sha256(password.encode()).hexdigest(),
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
    st.markdown("Axon AI - Your trusted healthcare companion !!!")
    st.caption("How can I help you with your pharmacy needs today?")
    st.markdown("---")
    
    # display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # User input
    if prompt := st.chat_input("Ask about medicines, place orders, or get health advice..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        # add to the chat_history
        user_ref = db.collection("users").document(st.session_state.user_email)
        user_ref.update({"chat_history": firestore.ArrayUnion([prompt])})

        with st.chat_message("🧑"):
            st.markdown(prompt)
        
        contents = [ types.Content(role="user", parts=[types.Part(text=prompt)]) ]

        # generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    tools = types.Tool(function_declarations=[
                        check_availability_function, place_order_function, track_order_function, cancel_order_function, get_health_advice_function
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
                    user_email = st.session_state.user_email
                        
                    for fn in response.function_calls:
                        i += 1
                        st.info(f"{i}. Excuting: {fn.name}() function")
                        functions_called.append(fn.name)
                        
                        tool_call = response.candidates[0].content.parts[i-1].function_call
                        if tool_call.name == "check_medicine_availability":
                            result = check_medicine_availability(**tool_call.args)
                        elif tool_call.name == "place_order":
                            result = place_order(**tool_call.args, user_email=user_email)
                        elif tool_call.name == "track_order":
                            result = track_order(**tool_call.args, user_email=user_email)
                        elif tool_call.name == "cancel_order":
                            result = cancel_order(**tool_call.args, user_email=user_email)
                        elif tool_call.name == "get_health_advice":
                            result = get_health_advice(**tool_call.args, user_email=user_email)

                        function_response_part = types.Part.from_function_response(
                            name=fn.name,
                            response={"result": result},
                        )

                        contents.append(response.candidates[0].content) # from the model
                        contents.append(types.Content(role="user", parts=[function_response_part])) # from the function
                    
                    final_response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        config=config,
                        contents=contents
                    )

                    st.session_state.messages.append({"role": "model", "content": final_response.text})

                    if len(functions_called) == 1:
                        st.info(f"Function executed: {', '.join(functions_called)}")
                    if len(functions_called) > 1:
                        st.info(f"Functions executed are: {', '.join(functions_called)}")
                        
                    st.markdown(final_response.text)                    
                except Exception as e:
                    error_msg = f"Sorry, I unable to process your request: {str(e)}, please try again."
                    st.warning(error_msg)
    
    with st.sidebar:
        st.title("Your Account")
        st.markdown(f"**Name:** {st.session_state.user_data.get('name', 'N/A')}")
        st.markdown(f"**Email:** {st.session_state.user_email}")
        st.markdown(f"**Age:** {st.session_state.user_data.get('age', 'N/A')}")
        st.markdown("---") 
        st.subheader("**What You Can Do!**")
        st.markdown("""
        - Check Medicine Presence
        - Place and Cancel Orders
        - Track your Orders
        - Get Health Advice
        """)
        st.markdown("---")
        if st.button("Refresh"):
            st.session_state.messages = []
            st.rerun()
        if st.button("Logout"):
            st.session_state.clear()
            st.rerun()
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center;">
            <p>📱 Join our <a href="https://t.me/axon_pharmacy" target="_blank">Telegram channel</a> for updates</p>
            <p>🌐 Visit our <a href="https://axonpharma.com" target="_blank">website</a></p>
            <p>📞 Contact us: +251111234567</p>
        </div>
        """, unsafe_allow_html=True)

def main():
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

if __name__ == "__main__":
    main()