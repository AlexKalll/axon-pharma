# scripts/user_functions.py

from datetime import datetime
import hashlib
from typing import Optional, Dict, Any
import uuid
from firebase_admin import firestore

from firebase.db_manager import db

def check_medicine_availability(medicine_name: str) -> Dict[str, Any]:
    try:
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
    except Exception as e:
        return {
            "success": False,
            "message": f"Error checking medicine: {str(e)}"
        }

def place_order(medicine_name: str, quantity: int, user_email: str) -> Dict[str, Any]:
    try:
        if quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be positive"
            }
        
        availability = check_medicine_availability(medicine_name)
        if not availability["success"]:
            return availability
        
        medicine_data = availability["data"]
        if medicine_data["stock"] < quantity:
            return {
                "success": False,
                "message": f"Not enough stock. Available: {medicine_data['stock']}"
            }
        
        order_id = str(uuid.uuid4())
        total_price = quantity * medicine_data["unit_price"]
        
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
        
        new_stock = medicine_data["stock"] - quantity
        name = medicine_name.lower().replace(' ', '_')
        db.collection("medicines").document(name).update({"stock": new_stock})
        db.collection("orders").document(order_id).set(order_data)
        
        user_ref = db.collection("users").document(user_email)
        user_ref.update({f"orders.{order_id}": medicine_name})
        
        return {
            "success": True,
            "order_id": order_id,
            "data": order_data,
            "message": f"Order placed successfully! Order ID: {order_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error placing order: {str(e)}"
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
        
        if order_dict["user_email"] != user_email:
            return {
                "success": False,
                "message": "This order doesn't belong to you"
            }
        
        return {
            "success": True,
            "data": order_dict,
            "message": f"Order status: {order_dict.get('status', 'unknown')}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error tracking order: {str(e)}"
        }

def cancel_order(order_id: str, user_email: str) -> Dict[str, Any]:
    try:
        track_result = track_order(order_id, user_email)
        if not track_result["success"]:
            return track_result
        
        order_data = track_result["data"]
        
        if order_data["status"].lower() not in ["pending", "processing"]:
            return {
                "success": False,
                "message": f"Cannot cancel order with status: {order_data['status']}"
            }
        
        db.collection("orders").document(order_id).update({
            "status": "cancelled",
            "updated_at": datetime.now()
        })
        
        medicine_name = order_data["medicine_name"]
        quantity = order_data["quantity"]
        
        medicine_ref = db.collection("medicines").document(medicine_name.lower().replace(' ', '_'))
        medicine_ref.update({"stock": firestore.Increment(quantity)})
        
        return {
            "success": True,
            "message": f"Order {order_id} cancelled successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error cancelling order: {str(e)}"
        }

def get_health_advice(user_email: str, symptoms: Optional[str] = None) -> Dict[str, Any]:
    try:
        user_ref = db.collection("users").document(user_email)
        user_data = user_ref.get().to_dict()
        
        if not user_data:
            return {
                "success": False,
                "message": "User data not found"
            }
        
        orders = user_data.get("orders", {})
        context = {
            "user": {
                "name": user_data.get("name"),
                "age": user_data.get("age"),
                "order_history": list(orders.values())
            },
            "symptoms": symptoms
        }
        
        return {
            "success": True,
            "data": context,
            "message": "Context collected for health advice"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error getting health advice: {str(e)}"
        }