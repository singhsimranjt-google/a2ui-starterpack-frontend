# -*- coding: utf-8 -*-
# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -*- coding: utf-8 -*-
"""Pizza Ordering Agent Tools."""

def show_toppings_form(
    pizza_name: str
) -> dict:
    """
    A passthrough tool to transition the UI to the toppings selection screen.

    Args:
        pizza_name: The name of the pizza the user wants to order.

    Returns:
        A dictionary containing the pizza name to be used by the LLM for the next UI.
    """
    print("\n--- 🛠️ TOOL CALL: show_toppings_form ---")
    print(f"Inputs: pizza_name='{pizza_name}'")
    result = {"status": "success", "pizza_name": pizza_name}
    print(f"Returns: {result}\n--------------------------------------\n")
    return result

def show_order_form(
    pizza_name: str,
    toppings: dict | None = None,
) -> dict:
    """
    A passthrough tool to transition the UI to the final order form. It processes
    the selected toppings into a simple list.
    
    Args:
        pizza_name: The name of the pizza selected by the user.
        toppings: A dictionary representing the toppings selected by the user, where keys are topping names and values are booleans.
    """
    if toppings is None:
        toppings = {}
        
    selected_toppings = [key for key, value in toppings.items() if value]
    if not selected_toppings:
        selected_toppings.append("None")
        
    result = {
        "status": "success",
        "pizza_name": pizza_name,
        "toppings": ", ".join(selected_toppings),
    }
    print("\n--- 🛠️ TOOL CALL: show_order_form ---")
    print(f"Inputs: pizza_name='{pizza_name}', toppings={toppings}")
    print(f"Returns: {result}\n--------------------------------------\n")
    return result

def place_order(
    pizza_name: str,
    toppings: str,
    quantity: str,
    customer_name: str,
    address: str,
) -> dict:
    """
    Places the final pizza order.

    Args:
        pizza_name: The name of the pizza.
        toppings: The comma-separated string of selected toppings.
        quantity: How many pizzas are being ordered. This will be a string from the UI.
        customer_name: The name for the order.
        address: The delivery address.

    Returns:
      A dictionary containing all the confirmed order details for display.
    """
    pizza_images = {
        "Margherita": (
            "https://images.unsplash.com/photo-1574071318508-1cdbab80d002?q=80&w=500&auto=format&fit=crop"
        ),
        "Pepperoni": (
            "https://images.unsplash.com/photo-1628840042765-356cda07504e?q=80&w=500&auto=format&fit=crop"
        ),
        "Vegetarian": (
            "https://images.unsplash.com/photo-1513104890138-7c749659a591?q=80&w=500&auto=format&fit=crop"
        ),
    }
    # Ensure quantity is a valid integer, default to 1 if not.
    try:
        order_quantity = int(quantity)
    except (ValueError, TypeError):
        order_quantity = 1

    result = {
        "status": "confirmed",
        "pizza_name": pizza_name,
        "pizza_image_url": pizza_images.get(pizza_name, ""),
        "toppings": toppings,
        "quantity": order_quantity,
        "customer_name": customer_name,
        "address": address,
    }
    print("\n--- 🛠️ TOOL CALL: place_order ---")
    print(f"Inputs: pizza_name='{pizza_name}', toppings='{toppings}', quantity='{quantity}', customer_name='{customer_name}', address='{address}'")
    print(f"Returns: {result}\n--------------------------------------\n")
    return result


def cancel_order() -> dict:
    """
    Cancels the current order process.

    Returns:
      A dictionary indicating the order was canceled.
    """
    print("\n--- 🛠️ TOOL CALL: cancel_order ---")
    print("Inputs: None")
    result = {"status": "canceled"}
    print(f"Returns: {result}\n--------------------------------------\n")
    return result
