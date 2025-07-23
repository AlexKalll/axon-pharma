telegram_post_function = {
    "name": "telegram_post",
    "description": """Create a pharmacy announcement as with those important instructiions in addition to the prompt:
    1. use stunning html tags icons etc
    2. Newlines for line breaks
    3. Relevant emojis
    4. Use the following information while creating the announcements:
    - name: Axon Pharmacy
    - location: 4kilo, Addis Ababa
    - telegram contact: @axon_pharmacy
    - website: https://axonpharma.com
    - phone: +251111234567
    - with hashtags #AxonPharmacy #VitaminC #Health #NewProduct #AddisAbaba etc""",
    "parameters": {
        "type": "object",
        "properties": {
            "message": {
                "type": "string",
                "description": "Formatted message content with Telegram-supported HTML and amazing emojis and icons",
            },
        },
        "required": ["message"]
    },
}

add_medicine_function = {
    "name": "add_medicine",
    "description": "Adds a new medicine to the pharmacy",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin",
            },
            "unit_price": {
                "type": "number",
                "description": "Unit price of the medicine eg 12.5, 10.0, 5.0",
            },
            "stock": {
                "type": "number",
                "description": "Quantity of the medicine eg 100, 200, 300",
            },
            "madein": {
                "type": "string",
                "description": "Country of origin eg Ethiopia, Kenya, Tanzania",
            },
            "category": {
                "type": "string",
                "description": "Category of the medicine eg antibiotics, vitamins, painkillers",
            },
            "description": {
                "type": "string",
                "description": "Description of the medicine",
            },
        },
        "required": ["name"]
    }
}

stock_out_function = {
    "name": "stock_out",
    "description": "Updates a medicine stock to 0 and notifying the users on telegram as the medicine is out of stock",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin",
            }
        },
        "required": ["name"]
    }
}

add_stock_function = {
    "name": "add_stock",
    "description": "Updates a medicine stock ",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin",
            },
            "quantity": {
                "type": "number",
                "description": "new quantity of the medicine to be added eg 100, 200, 300",
            }
        },
        "required": ["name", "quantity"]
    }
}

delete_medicine_function = {
    "name": "delete_medicine",
    "description": "Deletes a medicine from the pharmacy and notifying the users on telegram if it is extinict from the earch or it is expermented as not safe for consumption",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin"
            }
        },
        "required": ["name"]
    }
}

update_order_status_function = {
    "name": "update_order_status",
    "description": "Updates a medicine order status of a specific order from the orders collection ",
    "parameters": {
        "type": "object",
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The ID of the order to update.",
            },
            "status": {
                "type": "string",
                "description": "The new status of the order (e.g., 'pending', 'processing', 'completed', 'deliverd', 'shipped', 'cancelled').",
            },
        },
        "required": ["order_id", "status"]
    }
}

check_availability_function = {
    "name": "check_medicine_availability",
    "description": "Check if a medicine is available in the pharmacy",
    "parameters": {
        "type": "object", 
        "properties": {
            "medicine_name":
            {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin"
            }
        },
        "required": ["medicine_name"]
    }
}

place_order_function = {
    "name": "place_order",
    "description": "Places an order for a specified quantity of a medicine for the currently logged-in user",
    "parameters": {
        "type": "object", 
        "properties": { 
            "medicine_name": {
                "type": "string",
                "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin"
            },
            "quantity": {
                "type": "number",
                "description": "Quantity of the medicine to be ordered"
            },
        }, 
        "required": ["medicine_name", "quantity"]
    }
}

track_order_function = {
    "name": "track_order",
    "description": "Check the status of an order",
    "parameters": {
        "type": "object", 
        "properties": {
            "order_id": {
                "type": "string",
                "description": "The ID of the order to track."
            },
        }, 
        "required": ["order_id"]
    }
}

cancel_order_function = {
    "name": "cancel_order",
    "description": "Cancel an order",
    "parameters": {
        "type": "object", 
        "properties": { 
            "order_id": {
                "type": "string",
                "description": "The ID of the order to cancel."
            },
        }, 
        "required": ["order_id"]
    }
}

get_health_advice_function = {
    "name": "get_health_advice",
    "description": "Get health advice for a specific medicine without any parameters since we can get a user from his details"
}