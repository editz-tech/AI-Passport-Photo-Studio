#ifndef AppVersion
  #define AppVersion "1.0.0"
#endif

[Setup]
AppId={{7C6D0A7E-8B17-4E67-9F9B-1A2F4D8C6E31}
AppName=AI Passport Photo Studio
AppVersion={#AppVersion}
AppPublisher=AI Passport Photo Studio
DefaultDirName={localappdata}\Programs\AI Passport Photo Studio
DefaultGroupName=AI Passport Photo Studio
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64
OutputDir=..\dist\installer
OutputBaseFilename=AI-Passport-Photo-Studio-Setup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\AI-Passport-Photo-Studio.exe
CloseApplications=yes
SetupLogging=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "..\dist\AI-Passport-Photo-Studio.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\AI Passport Photo Studio"; Filename: "{app}\AI-Passport-Photo-Studio.exe"
Name: "{autodesktop}\AI Passport Photo Studio"; Filename: "{app}\AI-Passport-Photo-Studio.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\AI-Passport-Photo-Studio.exe"; Description: "Launch AI Passport Photo Studio"; Flags: nowait postinstall skipifsilent
