"""
Flux Open Home - Customer Store
=================================
Manages customer records for management mode.
Persists connection key data in /data/customers.json.
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime, timezone

from connection_key import decode_connection_key

CUSTOMERS_FILE = "/data/customers.json"


@dataclass
class Customer:
    id: str
    name: str
    connection_key_encoded: str
    url: str
    api_key: str
    added_at: str
    notes: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""
    phone: str = ""
    first_name: str = ""
    last_name: str = ""
    zone_count: Optional[int] = None
    last_seen_online: Optional[str] = None
    last_status: Optional[dict] = field(default=None)
    ha_token: str = ""
    connection_mode: str = "direct"  # "direct" or "nabu_casa"
    zone_aliases: dict = field(default_factory=dict)  # entity_id → alias name


def load_customers() -> list[Customer]:
    """Load all customers from persistent storage."""
    if not os.path.exists(CUSTOMERS_FILE):
        return []
    try:
        with open(CUSTOMERS_FILE, "r") as f:
            data = json.load(f)
        customers = []
        for c in data.get("customers", []):
            # Handle missing fields from older versions
            c.setdefault("ha_token", "")
            c.setdefault("connection_mode", "direct")
            c.setdefault("zone_aliases", {})
            c.setdefault("phone", "")
            c.setdefault("first_name", "")
            c.setdefault("last_name", "")
            customers.append(Customer(**c))
        return customers
    except (json.JSONDecodeError, IOError, TypeError):
        return []


def save_customers(customers: list[Customer]):
    """Save all customers to persistent storage."""
    os.makedirs(os.path.dirname(CUSTOMERS_FILE), exist_ok=True)
    data = {"customers": [asdict(c) for c in customers]}
    with open(CUSTOMERS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_customer(
    encoded_key: str,
    name: Optional[str] = None,
    notes: str = "",
) -> Customer:
    """Decode a connection key and add a new customer. Returns the Customer."""
    key_data = decode_connection_key(encoded_key)
    print(f"[CUST_STORE] Decoded key: url='{key_data.url}', mode='{key_data.mode}', ha_token={'SET('+str(len(key_data.ha_token))+'chars)' if key_data.ha_token else 'NONE'}")

    customers = load_customers()

    # Check for duplicate URL+key combinations
    for c in customers:
        if c.url == key_data.url and c.api_key == key_data.key:
            raise ValueError(
                f"This connection key is already registered (customer: {c.name})"
            )

    customer = Customer(
        id=str(uuid.uuid4()),
        name=name or key_data.label or f"Customer {len(customers) + 1}",
        connection_key_encoded=encoded_key,
        url=key_data.url,
        api_key=key_data.key,
        added_at=datetime.now(timezone.utc).isoformat(),
        notes=notes,
        address=key_data.address or "",
        city=key_data.city or "",
        state=key_data.state or "",
        zip=key_data.zip or "",
        phone=key_data.phone or "",
        first_name=key_data.first_name or "",
        last_name=key_data.last_name or "",
        zone_count=key_data.zone_count,
        ha_token=key_data.ha_token or "",
        connection_mode=key_data.mode or "direct",
    )
    customers.append(customer)
    save_customers(customers)
    return customer


def remove_customer(customer_id: str) -> bool:
    """Remove a customer by ID. Returns True if found and removed."""
    customers = load_customers()
    original_count = len(customers)
    customers = [c for c in customers if c.id != customer_id]
    if len(customers) == original_count:
        return False
    save_customers(customers)
    return True


def get_customer(customer_id: str) -> Optional[Customer]:
    """Get a single customer by ID."""
    customers = load_customers()
    for c in customers:
        if c.id == customer_id:
            return c
    return None


def update_customer(
    customer_id: str,
    name: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Customer]:
    """Update a customer's name or notes."""
    customers = load_customers()
    for c in customers:
        if c.id == customer_id:
            if name is not None:
                c.name = name
            if notes is not None:
                c.notes = notes
            save_customers(customers)
            return c
    return None


def update_customer_zone_aliases(
    customer_id: str,
    zone_aliases: dict,
) -> Optional[Customer]:
    """Update a customer's zone aliases (entity_id → display name)."""
    customers = load_customers()
    for c in customers:
        if c.id == customer_id:
            c.zone_aliases = zone_aliases
            save_customers(customers)
            return c
    return None


def update_customer_status(customer_id: str, status: dict):
    """Update cached status after a health check.

    Also syncs live contact info (phone, name, address) from the
    homeowner's system_status response, so the management dashboard
    always shows the latest data even if the connection key was
    generated before the homeowner filled in their details.
    """
    customers = load_customers()
    for c in customers:
        if c.id == customer_id:
            c.last_status = status
            if status.get("reachable") and status.get("authenticated"):
                c.last_seen_online = datetime.now(timezone.utc).isoformat()

                # Sync live contact/address info from homeowner status
                sys_status = status.get("system_status", {})
                if sys_status:
                    for field_name in ("phone", "first_name", "last_name",
                                       "address", "city", "state", "zip"):
                        live_val = sys_status.get(field_name, "")
                        if live_val:  # Only overwrite if homeowner has a value
                            setattr(c, field_name, live_val)

            save_customers(customers)
            return
