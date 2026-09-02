"""Publish one logistics update while recording the signals a creator needs."""
from __future__ import annotations

import traceback

from infrai import infrai


def render_shipment_update(order_id: str, status: str) -> str:
    """Keep the public update short enough for a creator-facing feed."""
    return f"Shipment {order_id}: {status}."


def publish_update(order_id: str, status: str) -> dict[str, str]:
    """Return the rendered post after reporting one success metric."""
    try:
        post = render_shipment_update(order_id, status)
        infrai.metrics.report(**{
            "name": "shipment_update_published",
            "value": 1,
            "type": "counter",
        })
        return {"order_id": order_id, "post": post}
    except Exception as exc:
        infrai.errors.capture(**{
            "message": str(exc),
            "exception": traceback.format_exc(),
        })
        raise


def use_new_digest(order_id: str) -> bool:
    """Read a flag value before enabling a new digest layout."""
    result = infrai.flags.get_value("new-shipment-digest")
    return bool(result.get("value", result.get("default_value", False)))


if __name__ == "__main__":
    print(publish_update("EU-1042", "arriving at the hub"))
