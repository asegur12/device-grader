# Grade My Device

## Problem

A user wants an all-purpose program, run from the terminal, that looks at their
computer's storage and hardware and tells them how well the device is doing and
what they should do next.

## Initial requirements

- **R1** The program asks the user for permission to read their files, storage and hardware before scanning anything.
- **R2** If the user declines, the program exits without scanning.
- **R3** If the user accepts, the program scans the device's files, storage and hardware.
- **R4** The program prints a storage bar showing used space and total space.
- **R5** The storage bar splits used space into five colored categories:
  images, screenshots and videos (red); documents and PDFs (orange);
  downloads, apps, installers and music (yellow); system files and programs (blue);
  duplicate and junk files (pink).
- **R6** The program gives a storage grade and a next-step summary (for example, remove junk files, or "good job").
- **R7** The program prints the device's name and model.
- **R8** The program prints the device's type, size and weight.
- **R9** The program prints the device's RAM, storage and price.
- **R10** The program prints a summary of the device and grades it against college and office-job standards.
- **R11** The program says whether the user should upgrade.
