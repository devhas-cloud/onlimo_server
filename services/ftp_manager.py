import os
import subprocess
import logging

logger = logging.getLogger(__name__)

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def add_ftp_user(username, password):
    script_path = os.path.join(SCRIPT_DIR, 'addftp.sh')

    if not os.path.exists(script_path):
        logger.error(f"addftp.sh not found at {script_path}")
        return False, "Script addftp.sh not found"

    try:
        result = subprocess.run(
            ['sudo', 'bash', script_path, username, password],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info(f"FTP user {username} created successfully")
            return True, result.stdout.strip()
        else:
            logger.error(f"Failed to create FTP user {username}: {result.stderr.strip()}")
            return False, result.stderr.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout creating FTP user {username}")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"Error creating FTP user {username}: {e}")
        return False, str(e)


def delete_ftp_user(username):
    script_path = os.path.join(SCRIPT_DIR, 'delftp.sh')

    if not os.path.exists(script_path):
        logger.error(f"delftp.sh not found at {script_path}")
        return False, "Script delftp.sh not found"

    try:
        result = subprocess.run(
            ['sudo', 'bash', script_path, username],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            logger.info(f"FTP user {username} deleted successfully")
            return True, result.stdout.strip()
        else:
            logger.error(f"Failed to delete FTP user {username}: {result.stderr.strip()}")
            return False, result.stderr.strip()

    except subprocess.TimeoutExpired:
        logger.error(f"Timeout deleting FTP user {username}")
        return False, "Timeout"
    except Exception as e:
        logger.error(f"Error deleting FTP user {username}: {e}")
        return False, str(e)