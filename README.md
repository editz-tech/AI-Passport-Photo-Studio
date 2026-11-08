# AI Passport Photo Studio

A Windows desktop utility for preparing passport-style photos.

## Download and install (Windows 10/11, 64-bit)

1. Open the repository's **Releases** page: https://github.com/editz-tech/AI-Passport-Photo-Studio/releases
2. Download **AI-Passport-Photo-Studio-Setup.exe** from the latest release.
3. Run the setup file and follow the installation prompts. The installer creates a Start Menu shortcut, offers a desktop shortcut, and includes an uninstaller.

The packaged installer includes the Python application runtime, background-removal dependencies, and the U2Net model. The installed application is designed to run without requiring Python or downloading the AI model on first launch.

**Windows security note:** The installer is not code-signed. Windows may display a SmartScreen or unknown-publisher warning. This is not the same as a malware detection; only install software downloaded from this repository's official Releases page.

## Features

- Open a photo and preview it.
- Replace the background with white using the bundled AI background-removal model.
- Crop to a 35:45 portrait ratio.
- Export a 413 × 531 pixel JPEG or PNG at 300 DPI.

## Current limitations

- Crop uses the image center; face/head alignment is not automatically detected.
- The software does not guarantee compliance with every country's passport-photo rules. Check the destination authority's official requirements before submitting a photo.

## Developer build

The GitHub Actions workflow builds the Windows executable, packages it with Inno Setup, uploads a workflow artifact, and publishes a versioned GitHub Release on changes to the main branch.

For a local source run, use Python 3.11 or newer and install the packages in `requirements.txt`.

## License

MIT (see `LICENSE`).
