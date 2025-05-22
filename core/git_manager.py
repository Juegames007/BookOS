import os
import subprocess
from typing import List, Union, Optional # Union y Optional pueden ser útiles para los tipos de retorno

class GitManager:
    def __init__(self, git_command: Optional[str] = None):
        """
        El constructor de la clase.
        - git_command: Permite opcionalmente especificar la ruta exacta al ejecutable de Git.
                       Si no se proporciona, intenta determinarlo automáticamente:
                       'git.exe' en Windows, 'git' en otros sistemas (Linux, macOS).
        """
        if git_command:
            self.git_command = git_command
        else:
            # os.name es 'nt' para Windows.
            self.git_command = 'git' if os.name != 'nt' else 'git.exe'

    def _ejecutar_comando(self, 
                          comando_args: List[str], 
                          text_output: bool = False, 
                          check_exceptions: bool = True,
                          cwd: Optional[str] = None) -> subprocess.CompletedProcess:
        """
        Este es un método privado (convención por el guion bajo) y es el corazón de la clase.
        Se encarga de ejecutar cualquier comando Git que se le pase.

        - comando_args: Una lista de strings que representan el comando y sus argumentos
                        (ej., ['commit', '-m', 'Mi mensaje']).
        - text_output: Si es True, la salida (stdout y stderr) del comando se decodificará como texto.
                       Si es False, será bytes.
        - check_exceptions: Si es True (por defecto), y Git devuelve un código de error (salida no cero),
                            se lanzará una excepción `subprocess.CalledProcessError`. Esto es útil
                            para detener la ejecución si un comando Git falla.
        - cwd: "Current Working Directory" (Directorio de Trabajo Actual). Es la ruta de la carpeta
               desde donde se debe ejecutar el comando Git. Es crucial para que Git opere
               sobre el repositorio correcto.
        - Retorna: Un objeto `subprocess.CompletedProcess` que contiene información sobre
                   el proceso ejecutado, incluyendo su salida, errores, y código de retorno.
        """
        full_command = [self.git_command] + comando_args # Une el comando git base con sus argumentos.
        try:
            # subprocess.run es la forma moderna y recomendada de ejecutar comandos externos.
            resultado = subprocess.run(
                full_command,
                stdout=subprocess.PIPE,    # Captura la salida estándar del comando.
                stderr=subprocess.PIPE,    # Captura la salida de error estándar.
                check=check_exceptions,    # Controla si se lanzan excepciones en errores.
                text=text_output,          # Controla el tipo de salida (texto o bytes).
                cwd=cwd                    # Establece el directorio de trabajo.
            )
            return resultado
        except FileNotFoundError:
            # Esta excepción ocurre si el sistema no puede encontrar el ejecutable 'git'
            # (o 'git.exe'). Usualmente significa que Git no está instalado o no está en el PATH.
            print(f"\033[1;31m❌ Error: El comando '{self.git_command}' no fue encontrado. "
                  "Asegúrate de que Git está instalado y en el PATH del sistema.\033[0m") # Mensaje en rojo.
            raise # Relanza la excepción para que la parte del código que llamó a este método sepa del fallo.
        except subprocess.CalledProcessError as e:
            # Esta excepción se captura si 'check_exceptions' es True y Git devuelve un error.
            # El error detallado usualmente ya fue impreso por Git en e.stderr.
            # La clase BackupManager, que usa GitManager, se encargará de mostrar este error.
            raise # Relanza la excepción.

    def _verificar_git_instalado(self, cwd: Optional[str] = None) -> bool:
        """Chequea si Git está instalado y accesible ejecutando 'git --version'."""
        try:
            self._ejecutar_comando(['--version'], cwd=cwd) # Si no lanza excepción, Git está.
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False # Si hay error, Git no está o no funciona.

    def _verificar_repositorio(self, cwd: Optional[str] = None) -> bool:
        """Chequea si el directorio 'cwd' (o el actual) es un repositorio Git."""
        try:
            # 'git rev-parse --is-inside-work-tree' es un comando estándar y fiable
            # para saber si estás dentro de un repositorio Git. Devuelve "true" si es así.
            resultado = self._ejecutar_comando(['rev-parse', '--is-inside-work-tree'], text_output=True, cwd=cwd)
            return resultado.stdout.strip() == 'true'
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _verificar_remoto(self, remote_name: str = 'origin', cwd: Optional[str] = None) -> bool:
        """Chequea si un repositorio remoto específico (por defecto 'origin') está configurado."""
        try:
            # 'git remote -v' lista los remotos configurados y sus URLs.
            resultado = self._ejecutar_comando(['remote', '-v'], text_output=True, cwd=cwd)
            return remote_name in resultado.stdout # Verifica si el nombre del remoto aparece en la salida.
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def verificar_requisitos(self, remote_name: str = 'origin', cwd: Optional[str] = None) -> bool:
        """
        Este método público consolida todas las verificaciones necesarias antes de
        intentar operaciones de backup.
        - remote_name: El nombre del remoto a verificar (usualmente 'origin').
        - cwd: El directorio del repositorio Git a verificar.
        """
        if not self._verificar_git_instalado(cwd=cwd):
            # El mensaje de error de Git no encontrado ya se imprime en _ejecutar_comando.
            return False
        if not self._verificar_repositorio(cwd=cwd):
            print("\033[1;31m❌ El directorio actual (o el especificado) no es un repositorio Git válido.\033[0m")
            return False
        if not self._verificar_remoto(remote_name, cwd=cwd):
            print(f"\033[1;31m❌ El repositorio remoto '{remote_name}' no está configurado correctamente.\033[0m")
            return False
        return True # Si todas las verificaciones pasan.

    def pull_rebase(self, remote: str = 'origin', branch: str = 'master', cwd: Optional[str] = None):
        """Ejecuta 'git pull --rebase' desde el 'remote' y 'branch' especificados."""
        return self._ejecutar_comando(['pull', remote, branch, '--rebase'], cwd=cwd)

    def add_all(self, cwd: Optional[str] = None):
        """Ejecuta 'git add .' para añadir todos los cambios en el directorio 'cwd' al staging area."""
        return self._ejecutar_comando(['add', '.'], cwd=cwd)

    def get_status_porcelain(self, cwd: Optional[str] = None) -> Optional[str]:
        """
        Ejecuta 'git status --porcelain'. Este formato es fácil de parsear por scripts
        para ver qué archivos han cambiado.
        Retorna la salida como string, o None si hay un error.
        """
        try:
            resultado = self._ejecutar_comando(['status', '--porcelain'], text_output=True, cwd=cwd)
            return resultado.stdout # La salida de texto del comando.
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None # Indica fallo.

    def commit(self, message: str, cwd: Optional[str] = None):
        """Ejecuta 'git commit -m "message"'."""
        return self._ejecutar_comando(['commit', '-m', message], cwd=cwd)

    def push(self, remote: str = 'origin', branch: str = 'master', cwd: Optional[str] = None):
        """Ejecuta 'git push' al 'remote' y 'branch' especificados."""
        return self._ejecutar_comando(['push', remote, branch], cwd=cwd)
