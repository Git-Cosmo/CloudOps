"""
CLI Execution Utilities

Provides functions for running CLI commands with proper logging and error handling.
"""

import logging
import subprocess
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)


def run_command(
    cmd: List[str],
    cwd: Optional[Path] = None,
    capture_output: bool = False,
    check: bool = True,
    env: Optional[dict] = None
) -> subprocess.CompletedProcess:
    """
    Run a shell command with logging and error handling.

    Args:
        cmd: Command and arguments as a list
        cwd: Working directory for the command
        capture_output: Whether to capture stdout/stderr
        check: Whether to raise an exception on non-zero exit
        env: Environment variables to set for the command

    Returns:
        CompletedProcess instance with command results

    Raises:
        subprocess.CalledProcessError: If check=True and command fails
    """
    cmd_str = ' '.join(cmd)
    logger.info(f"Running: {cmd_str}")
    if cwd:
        logger.info(f"  in directory: {cwd}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check,
            env=env
        )
        if capture_output and result.stdout:
            logger.debug(f"Output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"stderr: {e.stderr}")
        raise


def command_exists(command: str) -> bool:
    """
    Check if a command exists in the system PATH.

    Args:
        command: Command name to check

    Returns:
        True if command exists, False otherwise
    """
    try:
        result = subprocess.run(
            ['which', command],
            capture_output=True,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False
