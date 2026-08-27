import sqlite3
import unittest

from main import import_communities, init_schema, latest_price


class DataStoreTests(unittest.TestCase):
    def test_importing_same_community_twice_is_idempotent(self):
        connection = sqlite3.connect(":memory:")
        init_schema(connection)
        record = {
            "id": "community-test",
            "name": "测试小区",
            "plate": "测试片区",
            "center": [119.38, 25.72],
            "listingPrice": 12000,
            "transactionPrice": 11000,
            "listingCount": 4,
            "buildYear": 2020,
            "developer": "测试开发商",
            "propertyCompany": "测试物业",
            "tags": ["次新"],
            "lastUpdated": "2026-08-25",
            "source": "手动导入",
            "snapshots": [{"metric": "listing", "value": 12000, "capturedAt": "2026-08-25"}],
        }

        import_communities(connection, [record])
        import_communities(connection, [record])

        self.assertEqual(connection.execute("SELECT COUNT(*) FROM communities").fetchone()[0], 1)
        self.assertEqual(connection.execute("SELECT COUNT(*) FROM price_snapshots").fetchone()[0], 1)

    def test_latest_price_keeps_listing_and_transaction_separate(self):
        snapshots = [
            {"metric": "listing", "value": 12800, "capturedAt": "2026-01-01"},
            {"metric": "transaction", "value": 11200, "capturedAt": "2026-03-01"},
            {"metric": "listing", "value": 12500, "capturedAt": "2026-03-10"},
        ]

        self.assertEqual(latest_price(snapshots, "listing")["value"], 12500)
        self.assertEqual(latest_price(snapshots, "transaction")["value"], 11200)


if __name__ == "__main__":
    unittest.main()
