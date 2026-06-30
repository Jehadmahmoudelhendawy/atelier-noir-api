import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def create_test_shipment(order):
    """
    Creates a shipment in Shippo for the given order using REST API and returns the tracking info.
    """
    if not settings.SHIPPO_API_KEY:
        logger.error("Shippo API Key is not set in settings.")
        return None

    headers = {
        "Authorization": f"ShippoToken {settings.SHIPPO_API_KEY}",
        "Content-Type": "application/json"
    }

    address_from = {
        "name": "Atelier Noir Formal Wear",
        "street1": "215 Clayton St.",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94117",
        "country": "US",
        "phone": "+1 555 341 9393",
        "email": "contact@assistifystore.com",
    }

    address_to = {
        "name": order.user.username if order.user else "Guest Customer",
        "street1": "965 Mission St",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94103",
        "country": "US",
        "phone": "+1 555 341 9393",
        "email": order.customer_email,
    }

    parcel = {
        "length": "20",
        "width": "15",
        "height": "10",
        "distance_unit": "cm",
        "weight": "1.0",
        "mass_unit": "kg",
    }

    payload = {
        "address_from": address_from,
        "address_to": address_to,
        "parcels": [parcel],
        "async": False
    }

    try:
        logger.info(f"Creating Shippo shipment for order {order.order_number} via REST API...")
        resp = requests.post("https://api.goshippo.com/shipments/", json=payload, headers=headers)
        
        if resp.status_code != 201:
            logger.error(f"Failed to create shipment. Status: {resp.status_code}, Body: {resp.text}")
            return None
            
        shipment_data = resp.json()
        rates = shipment_data.get("rates", [])
        
        if not rates:
            logger.error(f"No shipping rates found for order {order.order_number}. Messages: {shipment_data.get('messages')}")
            return None
            
        usps_rate = next((r for r in rates if r.get("provider", "").lower() == "usps"), None)
        rate_id = usps_rate["object_id"] if usps_rate else rates[0]["object_id"]
        
        logger.info(f"Purchasing shipping label for order {order.order_number} using rate {rate_id}...")
        tx_resp = requests.post(
            "https://api.goshippo.com/transactions/", 
            json={"rate": rate_id, "async": False}, 
            headers=headers
        )
        
        if tx_resp.status_code != 201:
            logger.error(f"Failed to purchase label. Status: {tx_resp.status_code}, Body: {tx_resp.text}")
            return None
            
        transaction = tx_resp.json()
        
        if transaction.get("status") == "SUCCESS":
            tracking_number = transaction.get("tracking_number")
            tracking_url = transaction.get("tracking_url_provider")
            logger.info(f"Successfully generated label. Tracking: {tracking_number}")
            
            return {
                "tracking_number": tracking_number,
                "tracking_url": tracking_url,
                "transaction_id": transaction.get("object_id")
            }
        else:
            logger.error(f"Failed to purchase label: {transaction.get('messages')}")
            return None

    except Exception as e:
        logger.error(f"Shippo API Error: {str(e)}", exc_info=True)
        return None
