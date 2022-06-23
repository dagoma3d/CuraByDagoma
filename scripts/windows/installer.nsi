!addplugindir "nsisPlugins"

; The name of the installer
Name "${BUILD_NAME}"

; The file to write
OutFile "${BUILD_NAME}.exe"

; The default installation directory
!if ${BUILD_ARCHITECTURE} == 'x64'
  InstallDir $PROGRAMFILES64\${BUILD_NAME}
!else
  InstallDir $PROGRAMFILES32\${BUILD_NAME}
!endif

; Registry key to check for directory (so if you install again, it will
; overwrite the old one automatically)
InstallDirRegKey HKLM "Software\${BUILD_NAME}" "Install_Dir"

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

!define MUI_ICON "dist/resources/images/cura.ico"
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
!define MUI_FINISHPAGE_RUN_TEXT $(Exec_Cura)
!define MUI_FINISHPAGE_RUN_FUNCTION "LaunchLink"
!define MUI_FINISHPAGE_SHOWREADME ""
!define MUI_FINISHPAGE_SHOWREADME_TEXT $(Create_Shortcut_Desktop)
!define MUI_FINISHPAGE_SHOWREADME_FUNCTION "CreateShortcutDesktop"

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
LangString Create_Shortcut_Desktop ${LANG_ENGLISH} "Add a shortcut on Desktop"
LangString Create_Shortcut_Desktop ${LANG_FRENCH} "Ajouter un raccourci sur le Bureau"
LangString Install_FTDI_Drivers ${LANG_ENGLISH} "Install FTDI Drivers"
LangString Install_FTDI_Drivers ${LANG_FRENCH} "Installer les pilotes FTDI"
LangString Install_CH430_Drivers ${LANG_ENGLISH} "Install CH430 Drivers"
LangString Install_CH430_Drivers ${LANG_FRENCH} "Installer les pilotes CH430"
LangString Open_STL_files_with_Cura ${LANG_ENGLISH} "Open STL files with Cura by Dagoma"
LangString Open_STL_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers STL avec Cura by Dagoma"
LangString Open_OBJ_files_with_Cura ${LANG_ENGLISH} "Open OBJ files with Cura by Dagoma"
LangString Open_OBJ_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers OBJ avec Cura by Dagoma"
LangString Open_AMF_files_with_Cura ${LANG_ENGLISH} "Open AMF files with Cura by Dagoma"
LangString Open_AMF_files_with_Cura ${LANG_FRENCH} "Ouvrir les fichiers AMF avec Cura by Dagoma"
LangString Exec_Cura ${LANG_ENGLISH} "Start ${BUILD_NAME}"
LangString Exec_Cura ${LANG_FRENCH} "Lancer ${BUILD_NAME}"

; Reserve Files
!insertmacro MUI_RESERVEFILE_LANGDLL
ReserveFile '${NSISDIR}\Plugins\x86-unicode\InstallOptions.dll'
ReserveFile "header.bmp"

Function .onInit
  ;!insertmacro MUI_LANGDLL_DISPLAY
  Push $R0
  System::Call 'kernel32::GetUserDefaultUILanguage() i.r10'
  StrCmp $R0 ${LANG_FRENCH} 0 +3
  StrCpy $LANGUAGE ${LANG_FRENCH}
  Goto +2
  StrCpy $LANGUAGE ${LANG_ENGLISH}
  Pop $R0
FunctionEnd

;--------------------------------

; The stuff to install
Section "${BUILD_NAME}"
  ;Try to delete Profile
  RMDir /r "$PROFILE\.curaByDagoma\${BUILD_VERSION}"

  SectionIn RO

  ; Set output path to the installation directory.
  SetOutPath $INSTDIR

  ; Put file there
  File /r "dist\"

  ; Write the installation path into the registry
  WriteRegStr HKLM "SOFTWARE\${BUILD_NAME}" "Install_Dir" "$INSTDIR"

  ; Write the uninstall keys for Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "DisplayName" "${BUILD_NAME}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "Publisher" "Dagoma"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "DisplayVersion" "${BUILD_VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "DisplayIcon" "$INSTDIR\resources\images\cura.ico"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "UninstallString" '"$INSTDIR\uninstall.exe"'
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "EstimatedSize" 0x0001adb0
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "NoModify" 1
  WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}" "NoRepair" 1
  WriteUninstaller "uninstall.exe"

  ; Write start menu entries for all users
  SetShellVarContext all

  CreateDirectory "$SMPROGRAMS\${BUILD_NAME}"
  CreateShortCut "$SMPROGRAMS\${BUILD_NAME}\Uninstall ${BUILD_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\uninstall.exe" 0
  CreateShortCut "$SMPROGRAMS\${BUILD_NAME}\${BUILD_NAME}.lnk" "$INSTDIR\python\pythonw.exe" '-m "Cura.cura"' "$INSTDIR\resources\images\cura.ico" 0

  ; Give all users write permissions in the install directory, so they can read/write profile and preferences files.
  AccessControl::GrantOnFile "$INSTDIR" "(S-1-5-32-545)" "FullAccess"

SectionEnd

Function LaunchLink
  ; Write start menu entries for all users
  SetShellVarContext all
  Exec '"$WINDIR\explorer.exe" "$SMPROGRAMS\${BUILD_NAME}\${BUILD_NAME}.lnk"'
FunctionEnd

; create a shortcut on desktop if desired by user
Function CreateShortcutDesktop
  SetShellVarContext all
  CreateShortCut "$DESKTOP\${BUILD_NAME}.lnk" "$INSTDIR\python\pythonw.exe" '-m "Cura.cura"' "$INSTDIR\resources\images\cura.ico" 0
FunctionEnd

Section $(Install_FTDI_Drivers)
  ; Set output path to the driver directory.
  SetOutPath "$INSTDIR\drivers\"
  File /r "drivers\"

  ${If} ${RunningX64}
    ExecWait '"$INSTDIR\drivers\CDM21224_Setup.exe" /lm'
  ${Else}
    ExecWait '"$INSTDIR\drivers\CDM21224_Setup.exe" /lm'
  ${EndIf}
SectionEnd

Section $(Install_CH430_Drivers)
  SetOutPath "$INSTDIR\drivers\"
  File /r "drivers\"
  ${If} ${RunningX64}
    ExecWait '"$INSTDIR\drivers\CH34x_Install_Windows_v3_4.EXE" /lm'
  ${Else}
    ExecWait '"$INSTDIR\drivers\CH34x_Install_Windows_v3_4.EXE" /lm'
  ${EndIf}
SectionEnd

Section $(Open_STL_files_with_Cura)
	WriteRegStr HKCR .stl "" "Cura STL model file"
	DeleteRegValue HKCR .stl "Content Type"
	WriteRegStr HKCR "Cura STL model file\DefaultIcon" "" "$INSTDIR\resources\images\stl.ico,0"
	WriteRegStr HKCR "Cura STL model file\shell" "" "open"
	WriteRegStr HKCR "Cura STL model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

Section $(Open_OBJ_files_with_Cura)
	WriteRegStr HKCR .obj "" "Cura OBJ model file"
	DeleteRegValue HKCR .obj "Content Type"
	WriteRegStr HKCR "Cura OBJ model file\DefaultIcon" "" "$INSTDIR\resources\images\stl.ico,0"
	WriteRegStr HKCR "Cura OBJ model file\shell" "" "open"
	WriteRegStr HKCR "Cura OBJ model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

Section $(Open_AMF_files_with_Cura)
	WriteRegStr HKCR .amf "" "Cura AMF model file"
	DeleteRegValue HKCR .amf "Content Type"
	WriteRegStr HKCR "Cura AMF model file\DefaultIcon" "" "$INSTDIR\resources\images\stl.ico,0"
	WriteRegStr HKCR "Cura AMF model file\shell" "" "open"
	WriteRegStr HKCR "Cura AMF model file\shell\open\command" "" '"$INSTDIR\python\pythonw.exe" -c "import os; os.chdir(\"$INSTDIR\"); import Cura.cura; Cura.cura.main()" "%1"'
SectionEnd

;--------------------------------

; Uninstaller

Section "Uninstall"

  ; Remove registry keys
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${BUILD_NAME}"
  DeleteRegKey HKLM "SOFTWARE\${BUILD_NAME}"

  ; Write start menu entries for all users
  SetShellVarContext all
  ; Remove directories used
  RMDir /r "$SMPROGRAMS\${BUILD_NAME}"
  ; remove shortcut from desktop
  Delete "$DESKTOP\${BUILD_NAME}.lnk"
  RMDir /r "$INSTDIR"
  ;Try to delete Profile
  RMDir /r "$PROFILE\.curaByDagoma\${BUILD_VERSION}"
SectionEnd
