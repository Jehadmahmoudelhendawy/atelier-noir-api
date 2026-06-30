import os
import requests
from dotenv import load_dotenv
load_dotenv()
SHOP = os.getenv("SHOPIFY_STORE_DOMAIN")
TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")
VERSION = os.getenv("SHOPIFY_API_VERSION", "2026-04")
def shopify_graphql(query: str, variables: dict = None) -> dict:
    url = f"https://{SHOP}/admin/api/{VERSION}/graphql.json"
    headers = {
        "X-Shopify-Access-Token": TOKEN,
        "Content-Type": "application/json",
    }
    res = requests.post(
        url,
        json={"query": query, "variables": variables or {}},
        headers=headers,
        timeout=20,
    )
    res.raise_for_status()
    return res.json()
def get_shopify_products() -> list:
    query = """
    query {
      products(first: 50) {
        edges {
          node {
            id
            title
            description
            variants(first: 1) {
              edges {
                node {
                  id
                  price
                }
              }
            }
          }
        }
      }
    }
    """
    try:
        data = shopify_graphql(query)
        products = []
        for edge in data["data"]["products"]["edges"]:
            node = edge["node"]
            if not node["variants"]["edges"]:
                continue
            variant = node["variants"]["edges"][0]["node"]
            products.append({
                "id": node["id"],
                "variant_id": variant["id"],
                "name": node["title"],
                "price": variant["price"],
                "description": node["description"] or "",
            })
        return products
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("get_shopify_products error: %s", exc)
        return []
def search_shopify_products(query_text: str) -> list:
    query = """
    query($query: String!) {
      products(first: 50, query: $query) {
        edges {
          node {
            id
            title
            description
            variants(first: 1) {
              edges {
                node {
                  id
                  price
                }
              }
            }
          }
        }
      }
    }
    """
    try:
        data = shopify_graphql(query, {"query": query_text})
        products = []
        for edge in data["data"]["products"]["edges"]:
            node = edge["node"]
            if not node["variants"]["edges"]:
                continue
            variant = node["variants"]["edges"][0]["node"]
            products.append({
                "id": node["id"],
                "variant_id": variant["id"],
                "name": node["title"],
                "price": variant["price"],
                "description": node["description"] or "",
            })
        return products
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("search_shopify_products error: %s", exc)
        return []
def create_shopify_draft_order(
    variant_id: str,
    quantity: int,
    customer_name: str,
    phone: str,
    address: str,
    email: str = None,
) -> dict:
    mutation = """
    mutation draftOrderCreate($input: DraftOrderInput!) {
      draftOrderCreate(input: $input) {
        draftOrder {
          id
          name
          invoiceUrl
        }
        userErrors {
          field
          message
        }
      }
    }
    """
    first_name = ""
    last_name = ""
    if customer_name:
        name_parts = customer_name.strip().split()
        first_name = name_parts[0]
        if len(name_parts) > 1:
            last_name = " ".join(name_parts[1:])
    input_data = {
        "lineItems": [
            {
                "variantId": variant_id,
                "quantity": int(quantity),
            }
        ],
        "shippingAddress": {
            "address1": address,
            "phone": phone,
            "firstName": first_name,
            "lastName": last_name,
        },
    }
    if email:
        input_data["email"] = email
    result = shopify_graphql(mutation, {"input": input_data})
    if "errors" in result:
        raise Exception(f"Shopify GraphQL error: {result.get('errors')}")
    draft_create = result.get("data", {}).get("draftOrderCreate", {})
    user_errors = draft_create.get("userErrors", [])
    if user_errors:
        raise Exception(f"Shopify userErrors: {user_errors}")
    draft_order = draft_create.get("draftOrder")
    if not draft_order:
        raise Exception(f"No draftOrder in response: {result}")
    return {
        "draft_order_id": draft_order["id"],
        "draft_order_name": draft_order["name"],
        "invoice_url": draft_order["invoiceUrl"],
        "status": "created",
    }
def get_shopify_draft_order_status(draft_order_id: str) -> dict | None:
    query = """
    query($id: ID!) {
      draftOrder(id: $id) {
        id
        name
        invoiceUrl
        status
      }
    }
    """
    try:
        result = shopify_graphql(query, {"id": draft_order_id})
        if "errors" in result:
            return None
        return result.get("data", {}).get("draftOrder")
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error("get_shopify_draft_order_status error: %s", exc)
        return None
if __name__ == "__main__":
    products = get_shopify_products()
    print(f"Found {len(products)} products:")
    for i, p in enumerate(products, start=1):
        print(f"  {i}. {p['name']} — {p['price']} — variant: {p['variant_id']}")