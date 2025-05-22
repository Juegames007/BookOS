import subprocess # Necesario para capturar CalledProcessError específicamente
from .git_manager import GitManager # Importación relativa de GitManager

class BackupGitManager:
    def __init__(self, git_manager_instance: GitManager, repo_path: str = "."):
        """
        Inicializa el BackupGitManager.

        Args:
            git_manager_instance: Una instancia de la clase GitManager.
            repo_path: La ruta al repositorio Git. Por defecto es ".",
                       lo que significa el directorio actual.
        """
        self.commit_message: str = "Backup automático del sistema de biblioteca"
        self.git_manager: GitManager = git_manager_instance
        self.repo_path: str = repo_path # Directorio del repositorio a gestionar

    def realizar_backup(self, remote: str = 'origin', branch: str = 'master') -> bool:
        """
        Realiza el proceso de backup: pull, add, commit, push.

        Args:
            remote: El nombre del repositorio remoto (ej. 'origin').
            branch: El nombre de la rama a la que hacer push/pull (ej. 'master', 'main').

        Returns:
            True si el backup fue exitoso o no había cambios, False si ocurrió un error.
        """
        try:
            # 1. Verificar requisitos de Git en el repo_path especificado
            if not self.git_manager.verificar_requisitos(remote_name=remote, cwd=self.repo_path):
                # Los mensajes de error específicos ya se imprimen en verificar_requisitos
                return False

            # 2. Intentar Pull con Rebase
            # ADVERTENCIA: Como bien señalaste, 'pull --rebase' reescribe el historial.
            # Esta operación es segura si esta rama es tuya y no ha sido pusheada
            # o si estás trabajando en una rama que no es compartida públicamente de forma
            # que otros basen su trabajo en su historial previo.
            # Para un backup "automático" en un repositorio principal o personal,
            # esto puede ser aceptable para mantener un historial lineal.
            # Si es una rama colaborativa, considera 'git pull' (sin rebase) o 'git merge'.
            try:
                print(f"\033[1;34m📥 Obteniendo cambios del repositorio remoto ({remote}/{branch})...\033[0m")
                self.git_manager.pull_rebase(remote=remote, branch=branch, cwd=self.repo_path)
            except subprocess.CalledProcessError as e:
                # Decodificar stderr si es bytes (si text_output=False en _ejecutar_comando)
                # Si text_output=True, e.stderr ya es str.
                error_output = e.stderr if isinstance(e.stderr, str) else e.stderr.decode(errors='ignore').strip() if e.stderr else "Error desconocido"
                
                # Comprobar si el error es por estar al día o conflictos no resueltos
                if "already up to date" in error_output.lower():
                    print(f"\033[1;32m✅ El repositorio ya está actualizado con {remote}/{branch}.\033[0m")
                elif "conflict" in error_output.lower() and "rebase" in error_output.lower():
                     print(f"\033[1;33m⚠️ Conflicto durante el rebase con {remote}/{branch}. "
                          "Resuelve los conflictos manualmente y luego intenta el backup.\033[0m")
                     return False # No continuar si hay conflictos de rebase
                else:
                    print(f"\033[1;33m⚠️ No se pudieron obtener los cambios remotos de {remote}/{branch} ({error_output}). "
                          "Continuando con el backup local...\033[0m")
                # No retornamos False aquí necesariamente, podríamos intentar el commit y push local.

            # 3. Agregar todos los cambios al staging area
            self.git_manager.add_all(cwd=self.repo_path)

            # 4. Obtener el estado para ver si hay cambios para comitear
            status_output = self.git_manager.get_status_porcelain(cwd=self.repo_path)
            if status_output is None: # Error al obtener el status
                print("\033[1;31m❌ No se pudo determinar el estado del repositorio.\033[0m")
                return False
            
            if not status_output.strip(): # Si la salida está vacía, no hay cambios
                print("\033[1;33m✅ No hay cambios para respaldar.\033[0m")
                return True # Consideramos esto un "éxito" ya que no hay nada que hacer

            # 5. Comitear los cambios
            print(f"\033[1;34m📝 Comiteando cambios con mensaje: '{self.commit_message}'...\033[0m")
            self.git_manager.commit(self.commit_message, cwd=self.repo_path)
            
            # 6. Subir los cambios al repositorio remoto
            print(f"\033[1;34m📤 Subiendo cambios al repositorio remoto ({remote}/{branch})...\033[0m")
            self.git_manager.push(remote=remote, branch=branch, cwd=self.repo_path)

            print("\033[1;32m✅ Backup completado exitosamente.\033[0m")
            return True

        except subprocess.CalledProcessError as e:
            error_cmd = ' '.join(e.cmd) if e.cmd else "Comando Git desconocido"
            error_stderr = e.stderr if isinstance(e.stderr, str) else e.stderr.decode(errors='ignore').strip() if e.stderr else "Sin salida de error"
            
            if 'push' in error_cmd and ("rejected" in error_stderr or "non-fast-forward" in error_stderr):
                print(f"\033[1;31m❌ No se pudo subir el backup a {remote}/{branch}: Cambios remotos conflictivos. "
                      "Intenta un 'git pull' manual para integrar los cambios remotos y luego reintenta el backup.\033[0m")
            elif 'commit' in error_cmd and 'nothing to commit' in error_stderr:
                print("\033[1;33m✅ No había nuevos cambios para comitear después del pull.\033[0m")
                return True # No es un error fatal si no hay nada nuevo que comitear después de un pull.
            else:
                print(f"\033[1;31m❌ Error durante la operación Git ({error_cmd}): {error_stderr}\033[0m")
            return False
        except FileNotFoundError:
            # Este error (Git no encontrado) ya es manejado e impreso por GitManager.
            # No es necesario imprimirlo de nuevo aquí, solo asegurar que retornamos False.
            return False
        except Exception as e:
            # Captura cualquier otra excepción inesperada.
            print(f"\033[1;31m❌ Error inesperado durante el proceso de backup: {str(e)}\033[0m")
            return False
