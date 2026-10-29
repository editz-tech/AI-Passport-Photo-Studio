WhiteBG Studio — standalone Windows app

This folder is built by GitHub Actions on a Windows runner. The workflow creates a Windows executable and bundles the U2Net AI model so first-run background replacement can work offline.

Features
- Batch processing from a folder or selected images
- Pure white background
- Keeps source images untouched
- Saves JPEG files to a separate output folder
- Avoids overwriting existing output files by adding a numeric suffix
- Progress and error messages

Build result
After the GitHub Actions job completes, download the "WhiteBGStudio-Windows" artifact. It contains "WhiteBG Studio.exe". It is a portable executable, not an MSI installer.

Review photos before official use. AI segmentation may make mistakes around hair, glasses, veils, and similar-colored clothing. No official photo acceptance is guaranteed.
