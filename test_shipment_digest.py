import unittest
from unittest.mock import patch

from shipment_digest import publish_update, render_shipment_update


class ShipmentDigestTest(unittest.TestCase):
    def test_render_keeps_order_context(self):
        self.assertEqual(render_shipment_update("EU-1042", "sorted"), "Shipment EU-1042: sorted.")

    @patch("shipment_digest.infrai.metrics.report")
    def test_publish_reports_one_metric(self, report):
        result = publish_update("EU-1042", "sorted")
        report.assert_called_once()
        self.assertEqual(result["order_id"], "EU-1042")


if __name__ == "__main__":
    unittest.main()
