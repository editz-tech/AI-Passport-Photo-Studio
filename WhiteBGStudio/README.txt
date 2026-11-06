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


Windows publisher verification / Smart App Control

The build supports Authenticode signing. To sign the EXE, the repository owner must first obtain a genuine code-signing certificate from a trusted certificate authority or an eligible Microsoft Trusted Signing account. A self-signed certificate will not make Smart App Control trust the app on other PCs.

For a PFX code-signing certificate:
1. Convert the PFX file to a single-line Base64 string locally. Do not upload the PFX to the repository.
   PowerShell: [Convert]::ToBase64String([IO.File]::ReadAllBytes("publisher.pfx")) | Set-Clipboard
2. In GitHub, open the repository Settings > Secrets and variables > Actions.
3. Add repository secrets:
   - WINDOWS_CERTIFICATE_BASE64 = the Base64 string from step 1
   - WINDOWS_CERTIFICATE_PASSWORD = the PFX password
4. Run the "Build WhiteBG Studio for Windows" workflow again.
5. The build signs the EXE with SHA-256, adds a trusted timestamp, and verifies the signature before packaging.

Security notes
- Never commit a PFX file, certificate password, or Base64 certificate to source control.
- The workflow does not print the certificate or password in its logs and removes the temporary PFX after signing.
- If the two secrets are not configured, the build completes with an unsigned EXE and a warning. Smart App Control may still block that build.
- A valid signature identifies the publisher, but it does not guarantee immediate Smart App Control approval. Windows reputation and policy also affect whether an app runs.
- Do not disable Smart App Control as a workaround.
