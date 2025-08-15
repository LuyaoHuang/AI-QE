import os
import importlib
import sys
import subprocess
import inspect
import shlex
import logging
import paramiko


def load_modules(modules_list: list, module_path: str='.') -> object:
    """ Use importlib to load python modules
    """
    cmd_folder = os.path.realpath(module_path)
    sys.path.insert(0, cmd_folder)
    for module in modules_list:
        yield importlib.import_module(module)


def load_func_data(file_list: list, dir_path: str) -> object:
    """ Get function name and document then format them to dict list
    """
    for module in load_modules(file_list, dir_path):
        for _, func in inspect.getmembers(module, inspect.isfunction):
            yield {"name": f"{module.__name__}.{func.__name__}",
                   "doc": func.__doc__}


def load_module_data(file_list: list, dir_path: str) -> object:
    """ Use load_modules() function to load function and formate it to dict list
    """
    for module in load_modules(file_list, dir_path):
        yield {"name": module.__name__,
               "doc": module.__doc__}


def run_cmd(cmd_line: str, timeout: int = 60, cwd: str = None) -> tuple[int, str]:
    """ Use subprocess to run shell command with improved error handling

    Args:
        cmd_line: Command line string to execute
        timeout: Timeout in seconds (default: 60)
        cwd: Working directory for command execution (default: None)

    Returns:
        Tuple of (return_code, output_string)
    """
    try:
        # Handle command prefixes like $ or #
        cmd_line = cmd_line.strip()
        if cmd_line.startswith(('$', '#')):
            cmd_line = cmd_line[1:]

        # Use shlex.split() for proper handling of quotes and spaces
        cmd_list = shlex.split(cmd_line)

        logging.debug(f"Executing command: {cmd_list}")

        # Run command with timeout and proper error handling
        result = subprocess.run(
            cmd_list,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            cwd=cwd,
            text=True,  # Use text mode instead of bytes
            encoding='utf-8',
            errors='replace'  # Handle encoding errors gracefully
        )

        # Combine stdout and stderr
        output = result.stdout + result.stderr

        if result.returncode != 0:
            logging.warning(f"Command failed with return code {result.returncode}: {cmd_line}")

        return result.returncode, output
    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds: {cmd_line}"
        logging.error(error_msg)
        return -1, error_msg
    except FileNotFoundError:
        error_msg = f"Command not found: {cmd_line}"
        logging.error(error_msg)
        return -1, error_msg
    except Exception as e:
        error_msg = f"Error executing command '{cmd_line}': {str(e)}"
        logging.error(error_msg)
        return -1, error_msg


class RemoteExecutor:
    """
    Remote command execution and file transfer using SSH.

    This class provides functionality to execute commands and transfer files
    on remote hosts using SSH connections. It supports both key-based and
    password-based authentication.
    """
    def __init__(self, host: str, username: str, port: int = 22,
                 key_file: str = None, password: str = None):
        """
        Initialize SSH connection parameters.

        Args:
            host: Remote host address
            username: SSH username
            port: SSH port (default: 22)
            key_file: Path to SSH private key file
            password: SSH password (if not using key auth)
        """
        self.host = host
        self.username = username
        self.port = port
        self.key_file = key_file
        self.password = password
        self.client = None
        self.sftp = None

    def connect(self) -> bool:
        """
        Establish SSH connection to remote host.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_file and os.path.exists(self.key_file):
                # Key-based authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_file,
                    timeout=30
                )
            elif self.password:
                # Password-based authentication
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )
            else:
                logging.error("No authentication method provided (key_file or password)")
                return False

            self.sftp = self.client.open_sftp()
            logging.info(f"Successfully connected to {self.host}")
            return True

        except Exception as e:
            logging.error(f"Failed to connect to {self.host}: {str(e)}")
            return False

    def disconnect(self):
        """Close SSH and SFTP connections."""
        if self.sftp:
            self.sftp.close()
        if self.client:
            self.client.close()
        logging.info(f"Disconnected from {self.host}")

    def execute_command(self, command: str, timeout: int = 60, cwd: str = None) -> tuple[int, str]:
        """
        Execute command on remote host.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            cwd: Working directory for command execution

        Returns:
            Tuple of (return_code, output_string)
        """
        if not self.client:
            return -1, "No SSH connection established"

        try:
            # Change directory if specified
            if cwd:
                command = f"cd {cwd} && {command}"

            logging.debug(f"Executing remote command: {command}")

            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)

            # Wait for command completion
            exit_status = stdout.channel.recv_exit_status()

            # Read output
            output = stdout.read().decode('utf-8', errors='replace')
            error = stderr.read().decode('utf-8', errors='replace')

            combined_output = output + error

            if exit_status != 0:
                logging.warning(f"Remote command failed with exit status {exit_status}: {command}")

            return exit_status, combined_output

        except Exception as e:
            error_msg = f"Error executing remote command '{command}': {str(e)}"
            logging.error(error_msg)
            return -1, error_msg

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to remote host.

        Args:
            local_path: Local file path
            remote_path: Remote file path

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sftp:
            logging.error("No SFTP connection established")
            return False

        try:
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_dir(remote_dir)

            self.sftp.put(local_path, remote_path)
            logging.debug(f"Uploaded {local_path} to {remote_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to upload {local_path} to {remote_path}: {str(e)}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """
        Download file from remote host.

        Args:
            remote_path: Remote file path
            local_path: Local file path

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sftp:
            logging.error("No SFTP connection established")
            return False

        try:
            # Create local directory if it doesn't exist
            local_dir = os.path.dirname(local_path)
            if local_dir:
                os.makedirs(local_dir, exist_ok=True)

            self.sftp.get(remote_path, local_path)
            logging.debug(f"Downloaded {remote_path} to {local_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to download {remote_path} to {local_path}: {str(e)}")
            return False

    def create_remote_file(self, remote_path: str, content: str) -> bool:
        """
        Create file with content on remote host.

        Args:
            remote_path: Remote file path
            content: File content

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.sftp:
            logging.error("No SFTP connection established")
            return False

        try:
            # Create remote directory if it doesn't exist
            remote_dir = os.path.dirname(remote_path)
            if remote_dir:
                self._ensure_remote_dir(remote_dir)

            with self.sftp.open(remote_path, 'w') as remote_file:
                remote_file.write(content)

            logging.debug(f"Created remote file {remote_path}")
            return True

        except Exception as e:
            logging.error(f"Failed to create remote file {remote_path}: {str(e)}")
            return False

    def _ensure_remote_dir(self, remote_dir: str):
        """Ensure remote directory exists, create if necessary."""
        try:
            self.sftp.stat(remote_dir)
        except FileNotFoundError:
            # Directory doesn't exist, create it
            try:
                self.sftp.mkdir(remote_dir)
                logging.debug(f"Created remote directory {remote_dir}")
            except Exception as e:
                # Try to create parent directories recursively
                parent_dir = os.path.dirname(remote_dir)
                if parent_dir and parent_dir != remote_dir:
                    self._ensure_remote_dir(parent_dir)
                    self.sftp.mkdir(remote_dir)


def run_remote_cmd(command: str, remote_config: dict, timeout: int = 60, cwd: str = None) -> tuple[int, str]:
    """
    Execute command on remote host using SSH.

    Args:
        command: Command to execute
        remote_config: Remote execution configuration dict
        timeout: Command timeout in seconds
        cwd: Working directory for command execution

    Returns:
        Tuple of (return_code, output_string)
    """
    executor = RemoteExecutor(
        host=remote_config.get("host"),
        username=remote_config.get("username"),
        port=remote_config.get("port", 22),
        key_file=remote_config.get("key_file"),
        password=remote_config.get("password")
    )

    if not executor.connect():
        return -1, f"Failed to connect to remote host {remote_config.get('host')}"

    try:
        return executor.execute_command(command, timeout, cwd)
    finally:
        executor.disconnect()
