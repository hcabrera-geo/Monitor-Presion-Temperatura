; Instalador NSIS para Monitor de Presion y Temperatura
; Descarga NSIS desde: https://nsis.sourceforge.io/

!include "MUI2.nsh"

; Nombre y version
Name "Monitor de Presion y Temperatura"
OutFile "Monitor_Presion_Temperatura_Setup.exe"
InstallDir "$PROGRAMFILES\MonitorPresion"

; Variables
Var StartMenuFolder

; MUI Settings
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Spanish"

RequestExecutionLevel admin

; Installer sections
Section "Instalar Aplicacion"
  SetOutPath "$INSTDIR"
  SetOverwrite try
  
  ; Crear el desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Copiar todos los archivos
  File /oname=app.py "app.py"
  File /oname=requirements.txt "requirements.txt"
  File /oname=README.md "README.md"
  File /oname=Ejecutar.bat "Ejecutar.bat"
  File /oname=setup.bat "setup.bat"
  
  ; Crear carpeta en Menu Inicio
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
    CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Monitor.lnk" "$INSTDIR\Ejecutar.bat"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Configurar.lnk" "$INSTDIR\setup.bat"
    CreateShortcut "$SMPROGRAMS\$StartMenuFolder\Desinstalar.lnk" "$INSTDIR\Uninstall.exe"
  !insertmacro MUI_STARTMENU_WRITE_END
  
  ; Crear enlace en escritorio
  CreateShortcut "$DESKTOP\Monitor Presion.lnk" "$INSTDIR\Ejecutar.bat"
  
  ; Ejecutar setup.bat para instalar dependencias
  ExecWait '"$INSTDIR\setup.bat"'
  
SectionEnd

; Uninstaller section
Section "Uninstall"
  ; Eliminar archivos
  Delete "$INSTDIR\app.py"
  Delete "$INSTDIR\requirements.txt"
  Delete "$INSTDIR\README.md"
  Delete "$INSTDIR\Ejecutar.bat"
  Delete "$INSTDIR\setup.bat"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$DESKTOP\Monitor Presion.lnk"
  
  ; Eliminar directorio
  RMDir "$INSTDIR"
  
  ; Eliminar del Menu Inicio
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  RMDir /r "$SMPROGRAMS\$StartMenuFolder"
  
SectionEnd
