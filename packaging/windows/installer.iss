#define AppName "Gold & Diamond Browser"
#define AppVersion "0.5.0"
#define AppPublisher "AtDev Dev"
#define AppExeName "GoldDiamondBrowser.exe"

[Setup]
AppId={{7DCC79C1-7A90-4C93-8C19-0C0D2B4A0F10}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
DefaultDirName={autopf}\Gold & Diamond Browser
DefaultGroupName={#AppName}
OutputDir=..\..\dist
OutputBaseFilename=Gold-Diamond-Browser-Setup-{#AppVersion}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\\..\\assets\\gold-diamond-icon.ico
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\{#AppExeName}

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: checkedonce

[Files]
Source: "..\..\dist\GoldDiamondBrowser\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: postinstall nowait skipifsilent
