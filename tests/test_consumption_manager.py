import datetime
from unittest.mock import patch
import unittest

from opencontext.managers.consumption_manager import ConsumptionManager


class ConsumptionManagerReportWindowTest(unittest.TestCase):
    def test_daily_report_window_uses_previous_calendar_day(self):
        manager = ConsumptionManager.__new__(ConsumptionManager)

        report_date, start_time, end_time = manager._get_daily_report_window(
            datetime.datetime(2026, 5, 19, 8, 30, 0)
        )

        self.assertEqual(report_date, datetime.date(2026, 5, 18))
        self.assertEqual(start_time, datetime.datetime(2026, 5, 18, 0, 0, 0))
        self.assertEqual(end_time, datetime.datetime(2026, 5, 19, 0, 0, 0))

    def test_parse_daily_report_date_from_title(self):
        manager = ConsumptionManager.__new__(ConsumptionManager)

        self.assertEqual(
            manager._parse_daily_report_date("Daily Report - 2026-05-18"),
            datetime.date(2026, 5, 18),
        )
        self.assertIsNone(manager._parse_daily_report_date("日报 - 2026年05月18日"))

    def test_completed_daily_report_requires_matching_heading(self):
        manager = ConsumptionManager.__new__(ConsumptionManager)

        class Storage:
            def get_vaults(self, **_kwargs):
                return [
                    {
                        "title": "Daily Report - 2026-05-19",
                        "content": "# 日报 - 2026年05月18日\n\ncontent",
                    },
                    {
                        "title": "Daily Report - 2026-05-18",
                        "content": "No activity data available for the specified time range.",
                    },
                ]

        with patch("opencontext.managers.consumption_manager.get_storage", return_value=Storage()):
            self.assertFalse(
                manager._has_completed_daily_report_for_date(datetime.date(2026, 5, 19))
            )
            self.assertFalse(
                manager._has_completed_daily_report_for_date(datetime.date(2026, 5, 18))
            )

    def test_last_report_date_ignores_mismatched_heading(self):
        manager = ConsumptionManager.__new__(ConsumptionManager)

        class Storage:
            def get_vaults(self, **_kwargs):
                return [
                    {
                        "title": "Daily Report - 2026-05-19",
                        "content": "# 日报 - 2026年05月18日\n\ncontent",
                    },
                    {
                        "title": "Daily Report - 2026-05-18",
                        "content": "# 日报 - 2026年05月18日\n\ncontent",
                    },
                ]

        with patch("opencontext.managers.consumption_manager.get_storage", return_value=Storage()):
            self.assertEqual(manager._get_last_report_date(), datetime.date(2026, 5, 18))


if __name__ == "__main__":
    unittest.main()
