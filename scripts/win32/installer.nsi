!ifndef VERSION
  !define VERSION 'Dagoma'
!endif
!addplugindir "nsisPlugins"

; The name of the installer
Name "${VERSION}"

; The file to write
OutFile "${VERSION}.exe"

; The default installation directory
InstallDir $PROGRAMFILES\${VERSION}

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${VERSION}" "Install_Dir"

; Request application privileges for Windows Vista
RequestExecutionLevel admin

; Set the LZMA compressor to reduce size.
SetCompressor /SOLID lzma
;--------------------------------

!include "MUI2.nsh"
!include "Library.nsh"

;--------------------------------

; StrContains
; This function does a case sensitive searches for an occurrence of a substring in a string.
; It returns the substring if it is found.
; Otherwise it returns null("").
; Written by kenglish_hi
; Adapted from StrReplace written by dandaman32


Var STR_HAYSTACK
Var STR_NEEDLE
Var STR_CONTAINS_VAR_1
Var STR_CONTAINS_VAR_2
Var STR_CONTAINS_VAR_3
Var STR_CONTAINS_VAR_4
Var STR_RETURN_VAR

Function StrContains
  Exch $STR_NEEDLE
  Exch 1
  Exch $STR_HAYSTACK
  ; Uncomment to debug
  ;MessageBox MB_OK 'STR_NEEDLE = $STR_NEEDLE STR_HAYSTACK = $STR_HAYSTACK '
    StrCpy $STR_RETURN_VAR ""
    StrCpy $STR_CONTAINS_VAR_1 -1
    StrLen $STR_CONTAINS_VAR_2 $STR_NEEDLE
    StrLen $STR_CONTAINS_VAR_4 $STR_HAYSTACK
    loop:
      IntOp $STR_CONTAINS_VAR_1 $STR_CONTAINS_VAR_1 + 1
      StrCpy $STR_CONTAINS_VAR_3 $STR_HAYSTACK $STR_CONTAINS_VAR_2 $STR_CONTAINS_VAR_1
      StrCmp $STR_CONTAINS_VAR_3 $STR_NEEDLE found
      StrCmp $STR_CONTAINS_VAR_1 $STR_CONTAINS_VAR_4 done
      Goto loop
    found:
      StrCpy $STR_RETURN_VAR $STR_NEEDLE
      Goto done
    done:
   Pop $STR_NEEDLE ;Prevent "invalid opcode" errors and keep the
   Exch $STR_RETURN_VAR
FunctionEnd

!macro _StrContainsConstructor OUT NEEDLE HAYSTACK
  Push `${HAYSTACK}`
  Push `${NEEDLE}`
  Call StrContains
  Pop `${OUT}`
!macroend

!define StrContains '!insertmacro "_StrContainsConstructor"'
;--------------------------------

!define MUI_ICON "dist/resources/cura.ico"
!define MUI_BGCOLOR FFFFFF

; Directory page defines
!define MUI_DIRECTORYPAGE_VERIFYONLEAVE

; Header
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_HEADERIMAGE_BITMAP_NOSTRETCH
; Don't show the component description box
!define MUI_COMPONENTSPAGE_NODESC

;Do not leave (Un)Installer page automaticly
!define MUI_FINISHPAGE_NOAUTOCLOSE
!define MUI_UNFINISHPAGE_NOAUTOCLOSE

;Run Cura after installing
!define MUI_FINISHPAGE_RUN
!define MUI_FINISHPAGE_RUN_TEXT "Start ${VERSION}"
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"

; Pages
;!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Languages
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "English"

; Language strings
LangString Install_Arduino_Drivers ${LANG_ENGLISH} "Install Arduino Drivers"
LangString Install_Arduino_Drivers ${LANG_FRENCH} "Installer les pilotes Arduino"
LangString Open_STL_files_with_Cura ${LANG_ENGLISH} "Open STL files with Cura by Dagoma"
LangString Open_STL_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers STL avec Cura by Dagoma"
LangString Open_OBJ_files_with_Cura ${LANG_ENGLISH} "Open OBJ files with Cura by Dagoma"
LangString Open_OBJ_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers OBJ avec Cura by Dagoma"
LangString Open_AMF_files_with_Cura ${LANG_ENGLISH} "Open AMF files with Cura by Dagoma"
LangString Open_AMF_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers AMF avec Cura by Dagoma"

; Reserve Files
!insertmacro MUI_RESERVEFILE_LANGDLL
ReserveFile '${NSISDIR}\Plugins\InstallOptions.dll'
ReserveFile "header.bmp"

Function .onInit
  !insertmacro MUI_LANGDLL_DISPLAY
FunctionEnd

;--------------------------------

; The stuff to install
Section "${VERSION}"
  ;Try to delete Profile
  RMDir /r "$PROFILE\.curaByDagomaEasy200"

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR



  ; Put file there
  File /r "dist\"

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\${VERSION}" "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VERSION}" "DisplayName" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VERSION}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VERSION}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VERSION}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

  ; Write start menu entries for all users
  SetShellVarContext all

  CreateDirectory "$SMPROGRAMS\${VERSION}"
  CreateShortCut "$SMPROGRAMS\${VERSION}\Uninstall ${VERSION}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${VERSION}\${VERSION}.lnk" "$INSTDIR\python\pythonw.exe" '-m "Cura.cura"' "$INSTDIR\resources\cura.ico" 0

  ; Give all users write permissions in the install directory, so they can read/write profile and preferences files.
  AccessControl::GrantOnFile "$INSTDIR" "(S-1-5-32-545)" "FullAccess"

SectionEnd

Function LaunchLink
  ; Write start menu entries for all users
  SetShellVarContext all
  Exec '"$WINDIR\explorer.exe" "$SMPROGRAMS\${VERSION}\${VERSION}.lnk"'
FunctionEnd

Section $(Install_Arduino_Drivers)
  ; Set output path to the driver directory.
  SetOutPath "$INSTDIR\drivers\"
  File /r "drivers\"

  ${If} ${RunningX64}
    ExecWait '"$INSTDIR\drivers\CDM21224_Setup.exe" /lm'
  ${Else}
    ExecWait '"$INSTDIR\drivers\CDM21224_Setup.exe" /lm'
  ${EndIf}
SectionEnd

Section $(Open_STL_files_with_Cura)
	WriteRegStr HKCR .stl "" "Cura STL model file"
	DeleteRegValue HKCR .stl "Content Type"
	WriteRegStr HKCR "Cura STL model file\DefaultIcon" "" "$INSTDIR\resources\stl.ico,0"
	WriteRegStr HKCR "Cura STL model file\shell" "" "open"
	WriteRegStr HKCR "Cura STL model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

Section $(Open_OBJ_files_with_Cura)
	WriteRegStr HKCR .obj "" "Cura OBJ model file"
	DeleteRegValue HKCR .obj "Content Type"
	WriteRegStr HKCR "Cura OBJ model file\DefaultIcon" "" "$INSTDIR\resources\stl.ico,0"
	WriteRegStr HKCR "Cura OBJ model file\shell" "" "open"
	WriteRegStr HKCR "Cura OBJ model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

Section $(Open_AMF_files_with_Cura)
	WriteRegStr HKCR .amf "" "Cura AMF model file"
	DeleteRegValue HKCR .amf "Content Type"
	WriteRegStr HKCR "Cura AMF model file\DefaultIcon" "" "$INSTDIR\resources\stl.ico,0"
	WriteRegStr HKCR "Cura AMF model file\shell" "" "open"
	WriteRegStr HKCR "Cura AMF model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${VERSION}"
  DeleteRegKey HKLM "SOFTWARE\${VERSION}"

  ; Write start menu entries for all users
  SetShellVarContext all
  ; Remove directories used
  RMDir /r "$SMPROGRAMS\${VERSION}"
  RMDir /r "$INSTDIR"
  ;Try to delete Profile
  RMDir /r "$PROFILE\.curaByDagomaEasy200"
SectionEnd
