telegram_post_function = {
        "name": "telegram_post",
        "description": "Posts a message to Telegram channel and group",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string", 
                    "description": "Formatted message content with Telegram-supported HTML",
                },
            },
            "required": ["message"],
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
            "required": ["name", "unit_price", "stock", "madein", "category", "description"]
        }
    }


stock_out_function = {
        "name": "stock_out",
        "description": "Updates a medicine stock and notifying the users on telegram if it is out of stock",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the medicine eg Paracetamol, Ibuprofen, Aspirin",
                },
                "sold_out": {
                    "type": "boolean",
                    "description": "True if the medicine is out of stock, False if the medicine is in stock",
                }
            },
            "required": ["name", "sold_out"]
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
    }}


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
                    "description": "The new status of the order (e.g., 'pending', 'processing', 'completed', 'cancelled').",
                },
            },  

            "required": ["order_id", "status"]
        }
    }
