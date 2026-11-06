E-PIX BG STUDIO — standalone Windows app

This folder is built by GitHub Actions on a Windows runner. The workflow creates a Windows executable and bundles the U2Net AI model so first-run background replacement can work offline.

Features
- Batch processing from a folder or selected images
- Pure white background
- Keeps source images untouched
- Saves JPEG files to a separate output folder
- Avoids overwriting existing output files by adding a numeric suffix
- Progress and error messages
- Preserves the original hairline and fine hair detail by avoiding mask erosion or hard thresholding

Build result
After the GitHub Actions job completes, download the "E-PIX-BG-STUDIO-Windows" artifact. It contains "E-PIX BG STUDIO.exe". It is a portable executable, not an MSI installer.

Review photos before official use. AI segmentation may make mistakes around hair, glasses, veils, and similar-colored clothing. No official photo acceptance is guaranteed.

Windows publisher verification / Smart App Control

The build is configured to require Authenticode signing before packaging. To sign the EXE, the repository owner must first obtain a genuine code-signing certificate issued to their legal person or business by a trusted certificate authority. A self-signed certificate will not make Smart App Control trust the app on other PCs.

For a PFX code-signing certificate:
1. Obtain a standard or EV code-signing certificate from a reputable certificate authority. Complete its identity/business validation. The CA may supply a hardware token or cloud signing service instead of a PFX; follow that provider's instructions.
2. If the CA provides a PFX, convert it to a single-line Base64 string locally. Do not upload the PFX to the repository.
   PowerShell: [Convert]::ToBase64String([IO.File]::ReadAllBytes("publisher.pfx")) | Set-Clipboard
3. In GitHub, open the repository Settings > Secrets and variables > Actions.
4. Add repository secrets:
   - WINDOWS_CERTIFICATE_BASE64 = the Base64 string from step 2
   - WINDOWS_CERTIFICATE_PASSWORD = the PFX password
5. Run the "Build E-PIX BG STUDIO for Windows" workflow again.
6. The build signs the EXE with SHA-256, adds a trusted timestamp, and verifies the signature before packaging.

Security notes
- Never commit a PFX file, certificate password, or Base64 certificate to source control.
- The workflow does not print the certificate or password in its logs and removes the temporary PFX after signing.
- The build fails rather than publishing an unsigned EXE if the signing secrets are missing.
- A valid signature identifies the publisher and helps Windows establish publisher trust, but it does not guarantee immediate Smart App Control approval. Windows reputation and policy also affect whether an app runs.
- Do not disable Smart App Control as a workaround.
