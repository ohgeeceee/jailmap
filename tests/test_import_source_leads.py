import csv
import tempfile
import unittest
from pathlib import Path

from scripts.import_source_leads import load_leads


FIELDS = [
    "state",
    "county",
    "facility",
    "source_url",
    "source_owner",
    "source_kind",
    "access_status",
    "adapter_strategy",
    "publication_default",
    "evidence_url",
    "notes",
]


class SourceLeadImportTests(unittest.TestCase):
    def write_rows(self, rows):
        handle = tempfile.NamedTemporaryFile("w", newline="", delete=False)
        with handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return Path(handle.name)

    def valid_row(self):
        return {
            "state": "TX",
            "county": "Dallas",
            "facility": "Dallas County Jail",
            "source_url": "https://www.dallascounty.org/jaillookup/",
            "source_owner": "Dallas County Sheriff",
            "source_kind": "search_portal",
            "access_status": "needs_adapter",
            "adapter_strategy": "search_form",
            "publication_default": "staging_only",
            "evidence_url": "https://www.dallascounty.org/departments/sheriff/inmate-information/",
            "notes": "Official lookup; review before enabling.",
        }

    def test_loads_valid_source_lead(self):
        path = self.write_rows([self.valid_row()])
        self.assertEqual(load_leads(path)[0]["state"], "TX")

    def test_rejects_non_https_source_url(self):
        row = self.valid_row()
        row["source_url"] = "http://example.test/inmates"
        path = self.write_rows([row])
        with self.assertRaises(ValueError):
            load_leads(path)

    def test_rejects_publication_default_that_would_enable_feed(self):
        row = self.valid_row()
        row["publication_default"] = "public"
        path = self.write_rows([row])
        with self.assertRaises(ValueError):
            load_leads(path)


if __name__ == "__main__":
    unittest.main()
