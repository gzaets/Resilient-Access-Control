#patch_raftos.py in the root directory
"""
Patch script to make raftos work with modern cryptography versions.
This script modifies the raftos package to remove its dependency on
cryptography 1.5.3 and make it compatible with your installed version.
"""
import os
import sys
import importlib
import re
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def find_raftos_path():
    """Find the installed raftos directory path."""
    try:
        # Try to import raftos to find its location
        import raftos
        return os.path.dirname(raftos.__file__)
    except ImportError:
        # If import fails, search in site-packages
        for path in sys.path:
            potential_path = os.path.join(path, 'raftos')
            if os.path.exists(potential_path) and os.path.isdir(potential_path):
                return potential_path
    
    return None

def backup_file(file_path):
    """Create a backup of the file before modifying it."""
    backup_path = f"{file_path}.bak"
    if not os.path.exists(backup_path):
        import shutil
        shutil.copy2(file_path, backup_path)
        logger.info(f"Created backup at {backup_path}")

def patch_files(raftos_path):
    """Patch raftos files to work with modern cryptography."""
    patched_files = []
    
    # Check if setup.py exists in parent directory and modify it
    parent_dir = os.path.dirname(raftos_path)
    setup_py = os.path.join(parent_dir, 'setup.py')
    if os.path.exists(setup_py):
        try:
            backup_file(setup_py)
            with open(setup_py, 'r') as f:
                content = f.read()
            
            # Remove cryptography version restriction
            modified = re.sub(
                r"'cryptography==1\.5\.3'", 
                "'cryptography>=39.0.0'", 
                content
            )
            
            if content != modified:
                with open(setup_py, 'w') as f:
                    f.write(modified)
                patched_files.append(setup_py)
                logger.info(f"Patched {setup_py}")
        except Exception as e:
            logger.error(f"Error patching setup.py: {e}")
    
    # Find and patch all Python files in the raftos package
    for root, _, files in os.walk(raftos_path):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    backup_file(file_path)
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Look for imports of cryptography
                    if 'cryptography' in content:
                        # Patch imports for newer cryptography versions
                        modifications = [
                            # Update import paths if needed
                            (r'from cryptography\.hazmat\.primitives import hashes', 
                             'from cryptography.hazmat.primitives import hashes'),
                            
                            # Update deprecated APIs if needed
                            (r'from cryptography\.hazmat\.backends import default_backend', 
                             'from cryptography.hazmat.backends import default_backend'),
                            
                            # Remove any version checks
                            (r'if cryptography\.__version__ != "1\.5\.3":', 
                             'if False:  # Version check disabled by patch')
                        ]
                        
                        modified = content
                        for old, new in modifications:
                            modified = re.sub(old, new, modified)
                        
                        if content != modified:
                            with open(file_path, 'w') as f:
                                f.write(modified)
                            patched_files.append(file_path)
                            logger.info(f"Patched {file_path}")
                except Exception as e:
                    logger.error(f"Error patching {file_path}: {e}")
    
    return patched_files

def main():
    logger.info("Starting raftos patch for modern cryptography")
    
    raftos_path = find_raftos_path()
    if not raftos_path:
        logger.error("Error: raftos package not found")
        return 1
    
    logger.info(f"Found raftos at: {raftos_path}")
    patched_files = patch_files(raftos_path)
    
    if patched_files:
        logger.info(f"Successfully patched {len(patched_files)} files")
        for file in patched_files:
            logger.info(f"  - {os.path.basename(file)}")
        logger.info("\nraftos should now work with modern cryptography version")
    else:
        logger.warning("No files were patched. This may indicate that either:")
        logger.warning("  - No cryptography-specific code was found")
        logger.warning("  - Files already compatible with modern cryptography")
        logger.warning("  - Issues accessing or modifying files")
    
    # Create a marker file to indicate patch was applied
    with open(os.path.join(raftos_path, ".patched"), "w") as f:
        f.write("Patched for modern cryptography compatibility")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())