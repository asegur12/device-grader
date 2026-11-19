"""Tests for grade_my_device.py.

Every test name starts with the requirement it checks (r1 = R1 in problem.md).
No test scans the real disk or reads real hardware: each one uses fake data
with known numbers, so we know exactly what the output should be.

Run from the repository folder:
    python -m unittest discover -s tests -v
"""

import io
import os
import re
import sys
import unittest
from contextlib import redirect_stdout
from unittest import mock

# Let the tests import grade_my_device.py from the folder above tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grade_my_device as gmd  # noqa: E402

GB = 1024 ** 3
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def plain(text):
    """Remove terminal color codes so we can compare plain text."""
    return ANSI.sub("", text)


def capture(func, *args):
    """Run func and return everything it printed."""
    out = io.StringIO()
    with redirect_stdout(out):
        func(*args)
    return out.getvalue()


def fake_scan(total=500, used=200, media=40, docs=10, downloads=20, system=128, junk=2):
    """A StorageScan filled with made-up sizes (in GB) instead of a real scan."""
    scan = gmd.StorageScan()
    scan.total, scan.used, scan.free = total * GB, used * GB, (total - used) * GB
    scan.sizes = {"media": media * GB, "docs": docs * GB, "downloads": downloads * GB,
                  "system": system * GB, "junk": junk * GB}
    return scan


def strong_laptop():
    """A modern laptop that should meet college and office standards."""
    return {
        "maker": "Dell Inc.", "family": "", "model": "XPS 13 9340",
        "type": "Laptop", "is_laptop": True, "screen_in": 13.4,
        "resolution": (1920, 1200), "battery": True,
        "os": "Windows 11 Home", "os_family": "windows",
        "cpu": "13th Gen Intel(R) Core(TM) i7-1360P", "cores": 12, "threads": 16,
        "ram_gb": 15.6, "storage_gb": 512, "storage_type": "NVMe SSD",
        "gpu": "Intel Iris Xe Graphics",
    }


def weak_laptop():
    """An old, low-end laptop that should fail both standards."""
    hw = strong_laptop()
    hw.update({
        "maker": "Acer", "model": "Aspire 1", "screen_in": 14.0,
        "resolution": (1366, 768), "os": "Windows 10 Home",
        "cpu": "Intel(R) Celeron(R) N4020", "cores": 2, "threads": 2,
        "ram_gb": 3.8, "storage_gb": 64, "storage_type": "HDD", "gpu": "",
    })
    return hw


class PermissionTests(unittest.TestCase):

    def run_main(self, answer):
        """Run main() with a typed answer. Returns (printed text, events in order)."""
        events = []

        def fake_input(prompt):
            events.append("asked: " + prompt)
            return answer

        def fake_hardware():
            events.append("read hardware")
            return strong_laptop()

        def fake_run(scan):
            events.append("scanned storage")

        out = io.StringIO()
        with mock.patch("builtins.input", fake_input), \
                mock.patch.object(gmd, "enable_terminal"), \
                mock.patch.object(gmd, "collect_hardware", fake_hardware), \
                mock.patch.object(gmd.StorageScan, "run", fake_run), \
                mock.patch.object(gmd, "print_storage_report"), \
                mock.patch.object(gmd, "print_device_report"), \
                redirect_stdout(out):
            try:
                gmd.main()
                exit_code = None
            except SystemExit as e:
                exit_code = e.code
        return out.getvalue(), events, exit_code

    def test_r1_asks_permission_before_scanning(self):
        """R1: the permission question comes before any hardware or storage reading."""
        printed, events, _ = self.run_main("y")
        self.assertTrue(events[0].startswith("asked:"))
        self.assertIn("permission", events[0].lower())
        self.assertEqual(events[1:], ["read hardware", "scanned storage"])
        self.assertIn("READ-ONLY", printed)

    def test_r2_declining_exits_without_scanning(self):
        """R2: answering n exits cleanly and nothing is read."""
        printed, events, exit_code = self.run_main("n")
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(events), 1)          # only the question
        self.assertIn("Nothing was scanned", printed)

    def test_r2_empty_answer_counts_as_declining(self):
        """R2: just pressing Enter is not permission."""
        _, events, exit_code = self.run_main("")
        self.assertEqual(exit_code, 0)
        self.assertEqual(len(events), 1)

    def test_r3_accepting_scans_hardware_and_storage(self):
        """R3: answering y reads the hardware and scans storage."""
        _, events, exit_code = self.run_main("y")
        self.assertIsNone(exit_code)
        self.assertIn("read hardware", events)
        self.assertIn("scanned storage", events)


class StorageBarTests(unittest.TestCase):

    def test_r4_bar_shows_used_and_total(self):
        """R4: the report states used space and total space."""
        printed = plain(capture(gmd.draw_storage_bar, fake_scan()))
        self.assertIn("200.0 GB used of 500.0 GB", printed)

    def test_r4_bar_is_always_the_same_width(self):
        """R4: the bar is 60 cells wide, filled for used space and shaded for free."""
        printed = plain(capture(gmd.draw_storage_bar, fake_scan()))
        bar = re.search(r"\[(.*)\]", printed).group(1)
        self.assertEqual(len(bar), 60)
        self.assertEqual(bar.count("█") + bar.count("░"), 60)

    def test_r5_bar_has_five_categories_in_the_right_colors(self):
        """R5: red, orange, yellow, blue, pink, each with its label."""
        expected = {
            "media": ("Images, screenshots & videos", "196"),        # red
            "docs": ("Documents & PDFs", "208"),                     # orange
            "downloads": ("Downloads, apps, installers & music", "226"),  # yellow
            "system": ("System, programs & other", "33"),            # blue
            "junk": ("Duplicate & junk files", "213"),               # pink
        }
        printed = capture(gmd.draw_storage_bar, fake_scan())
        for key, (label, color) in expected.items():
            self.assertEqual(gmd.CATEGORIES[key], (label, f"\033[38;5;{color}m"))
            self.assertIn(label, printed)
            self.assertIn(f"\033[38;5;{color}m█", printed)

    def test_r5_files_are_sorted_into_the_right_category(self):
        """R5: file type and location decide the category."""
        self.assertEqual(gmd.classify("/users/me/pictures/cat.jpg", ".jpg", True), "media")
        self.assertEqual(gmd.classify("/users/me/videos/trip.mp4", ".mp4", True), "media")
        self.assertEqual(gmd.classify("/users/me/documents/essay.pdf", ".pdf", True), "docs")
        self.assertEqual(gmd.classify("/users/me/music/song.mp3", ".mp3", True), "downloads")
        self.assertEqual(gmd.classify("/users/me/downloads/notes.pdf", ".pdf", True),
                         "downloads")
        self.assertEqual(gmd.classify("/windows/system32/kernel32.dll", ".dll", False),
                         "system")
        self.assertEqual(gmd.classify("/users/me/report.tmp", ".tmp", True), "junk")


class StorageGradeTests(unittest.TestCase):

    def test_r6_healthy_storage_gets_an_a_and_good_job(self):
        """R6: a roomy, tidy drive scores A and is told 'good job'."""
        score, reasons, _, _ = gmd.grade_storage(fake_scan())
        self.assertEqual((score, gmd.letter(score), reasons), (100, "A", []))
        printed = plain(capture(gmd.print_storage_report, fake_scan()))
        self.assertIn("Storage grade: A", printed)
        self.assertIn("Good job", printed)

    def test_r6_full_cluttered_storage_gets_an_f_and_cleanup_advice(self):
        """R6: a nearly full drive full of junk scores F and is told to clean up."""
        scan = fake_scan(total=500, used=480, media=40, docs=20, downloads=20,
                         system=300, junk=100)
        scan.junk_only = 100 * GB
        scan.junk_places = {"Temporary files": 100 * GB}
        score, reasons, _, _ = gmd.grade_storage(scan)
        self.assertEqual(gmd.letter(score), "F")
        self.assertEqual(len(reasons), 2)          # too full, too much junk
        printed = plain(capture(gmd.print_storage_report, scan))
        self.assertIn("Storage grade: F", printed)
        self.assertIn("What to do next", printed)
        self.assertIn("Clear about 100.0 GB of junk", printed)
        self.assertNotIn("Good job", printed)


class DeviceReportTests(unittest.TestCase):

    def test_r7_prints_device_name_and_model(self):
        """R7: name (maker + model, without 'Inc.') and model."""
        printed = plain(capture(gmd.print_device_report, strong_laptop()))
        self.assertIn("Device: Dell XPS 13 9340", printed)
        self.assertIn("Model:  XPS 13 9340", printed)

    def test_r8_prints_type_size_and_weight(self):
        """R8: type, screen size and an estimated weight."""
        printed = plain(capture(gmd.print_device_report, strong_laptop()))
        self.assertIn("Type ............ Laptop", printed)
        self.assertIn('13.4" screen, 1920x1200', printed)
        self.assertIn("about 1.3 kg", printed)
        self.assertEqual(gmd.estimate_weight_kg(strong_laptop()), 1.3)

    def test_r9_prints_ram_storage_and_price(self):
        """R9: RAM (rounded up to the installed size), storage and a price range."""
        printed = plain(capture(gmd.print_device_report, strong_laptop()))
        self.assertIn("16 GB installed (15.6 GB usable)", printed)
        self.assertIn("512 GB NVMe SSD", printed)
        lo, hi = gmd.estimate_price(strong_laptop())
        self.assertLess(lo, hi)
        self.assertIn(f"about ${lo:,} - ${hi:,}", printed)

    def test_r10_strong_device_meets_college_and_office_standards(self):
        """R10: a summary, both standards met, and a grade of A."""
        score, _, office, college = gmd.grade_hardware(strong_laptop())
        self.assertEqual((score, office, college), (100, True, True))
        printed = plain(capture(gmd.print_device_report, strong_laptop()))
        self.assertIn("Summary", printed)
        self.assertIn("Office-job standard (8 GB RAM, 256 GB SSD, 4+ cores): MEETS", printed)
        self.assertIn("College standard (16 GB RAM, 512 GB SSD, 4+ core modern CPU): MEETS",
                      printed)
        self.assertIn("Device grade: A", printed)

    def test_r10_weak_device_meets_neither_standard(self):
        """R10: an old low-end laptop fails both standards and gets an F."""
        score, _, office, college = gmd.grade_hardware(weak_laptop())
        self.assertEqual((office, college), (False, False))
        self.assertEqual(gmd.letter(score), "F")
        printed = plain(capture(gmd.print_device_report, weak_laptop()))
        self.assertEqual(printed.count("DOES NOT MEET"), 2)

    def test_r11_strong_device_needs_no_upgrade(self):
        """R11: a device that meets the standards is told no upgrade is needed."""
        printed = plain(capture(gmd.print_device_report, strong_laptop()))
        self.assertIn("Should you upgrade?", printed)
        self.assertIn("No upgrade needed", printed)

    def test_r11_weak_device_is_told_to_upgrade(self):
        """R11: a weak device is told to upgrade, with specific reasons."""
        printed = plain(capture(gmd.print_device_report, weak_laptop()))
        self.assertIn("An upgrade or replacement is recommended", printed)
        self.assertIn("Swap the hard drive for an SSD", printed)
        self.assertIn("RAM is below the 8 GB minimum", printed)


if __name__ == "__main__":
    unittest.main()
