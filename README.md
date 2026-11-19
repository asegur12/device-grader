# Grade My Device
This is the third of three projects for my CSC 299 Ai lab final project. This program is one that takes in the storage and hardware data from the device your using, and creates a grade based of that data

## How to run

Works on **Windows 10/11, macOS and Linux**. Requires Python 3.8+ (standard library only, no installs needed).
On Mac/Linux use `python3 grade_my_device.py`.

```
python grade_my_device.py
```

The program asks for permission first. Answer `n` and it closes without scanning anything.
Answer `y` and it scans every local drive (read-only) and your hardware, then prints:

1. **Storage usage**: a colored bar of used vs. total space, split into
   red (images/videos), orange (documents/PDFs), yellow (downloads/apps/installers/music),
   blue (system/programs/other) and pink (duplicate and junk files), plus a storage grade and next steps.
2. **Device report**: device name and model, type/size/weight, CPU/RAM/storage/price,
   a summary, a grade against college and office-job standards, and upgrade advice.

## How to run the tests

From this folder (standard library `unittest`, no installs needed):

```
python -m unittest discover -s tests -v
```

The tests use fake hardware and storage data, so they never scan your real disk.
Each test name starts with the requirement it checks (for example `test_r2_...` checks
R2 in `problem.md`).

### Safety
- Read-only: nothing is moved, changed or deleted.
- Nothing is written to disk or sent anywhere. Collected data is erased from memory once the report is printed.

### Notes
- Weight and price aren't stored by the operating system, so they're estimated from the device type, screen size and parts.
- A full scan takes about 1–2 minutes on a typical 512 GB drive.
- **macOS:** for a complete scan, give your Terminal app Full Disk Access
  (System Settings > Privacy & Security > Full Disk Access). Only the Mac's internal
  disk is scanned, and iCloud files that aren't downloaded are skipped.
- **Linux:** runs as a normal user. Only internal disks are scanned (USB drives,
  network shares and snap images are skipped); folders you can't read count as system space.
- Tested on Windows 11. The macOS and Linux code paths are tested with simulated system data.
