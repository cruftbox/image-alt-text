"""
Windows installer for Image Alt Text Generator.

Adds/removes right-click context menu integration for image files.
"""

import sys
import os
import winreg
import shutil


# File extensions to register
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

MENU_NAME = "GenerateAltText"
MENU_TEXT = "Generate Alt Text"
ICON = "imageres.dll,67"


def get_python_path() -> str:
    """Get the path to the Python executable."""
    return sys.executable


def get_script_path() -> str:
    """Get the path to the image-alt-text script."""
    # When installed via pip, the script is in the Scripts folder
    scripts_dir = os.path.dirname(get_python_path())
    script_path = os.path.join(scripts_dir, "Scripts", "image-alt-text.exe")

    if os.path.exists(script_path):
        return script_path

    # Try without Scripts subfolder (some installations)
    script_path = os.path.join(scripts_dir, "image-alt-text.exe")
    if os.path.exists(script_path):
        return script_path

    # Fall back to using python -m
    return None


def create_command() -> str:
    """Create the command to run when the context menu item is clicked."""
    script_path = get_script_path()

    if script_path:
        return f'"{script_path}" "%1"'
    else:
        # Use python -m as fallback
        python_path = get_python_path()
        return f'"{python_path}" -m image_alt_text.cli "%1"'


def install_for_extension(ext: str) -> bool:
    """Install context menu for a specific file extension."""
    try:
        key_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell\\{MENU_NAME}"

        # Create the shell key
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_TEXT)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, ICON)
        winreg.CloseKey(key)

        # Create the command key
        command_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
        winreg.SetValueEx(command_key, "", 0, winreg.REG_SZ, create_command())
        winreg.CloseKey(command_key)

        return True
    except Exception as e:
        print(f"  Error for {ext}: {e}")
        return False


def uninstall_for_extension(ext: str) -> bool:
    """Remove context menu for a specific file extension."""
    try:
        key_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell\\{MENU_NAME}"

        # Delete command subkey first
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"{key_path}\\command")
        except FileNotFoundError:
            pass

        # Delete main key
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
        except FileNotFoundError:
            pass

        return True
    except Exception as e:
        print(f"  Error for {ext}: {e}")
        return False


def check_api_key() -> bool:
    """Check if the API key is configured."""
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def install():
    """Install the Windows context menu integration."""
    print("Image Alt Text Generator - Installer")
    print("=" * 45)
    print()

    # Check for API key
    if not check_api_key():
        print("WARNING: ANTHROPIC_API_KEY environment variable not set!")
        print()
        print("To set it permanently:")
        print("  1. Open Start Menu, search 'environment variables'")
        print("  2. Click 'Edit the system environment variables'")
        print("  3. Click 'Environment Variables...'")
        print("  4. Under 'User variables', click 'New...'")
        print("  5. Name: ANTHROPIC_API_KEY")
        print("  6. Value: your-api-key-here")
        print()
        print("Get an API key at: https://console.anthropic.com/")
        print()

    print("Installing context menu for image files...")
    print()

    success_count = 0
    for ext in IMAGE_EXTENSIONS:
        if install_for_extension(ext):
            print(f"  [OK] {ext}")
            success_count += 1
        else:
            print(f"  [FAIL] {ext}")

    print()
    if success_count == len(IMAGE_EXTENSIONS):
        print("Installation complete!")
        print()
        print("Right-click any image file to see 'Generate Alt Text' option.")
        print()
        print("NOTE: On Windows 11, you may need to click 'Show more options'")
        print("      to see the menu item, unless you've enabled the classic")
        print("      context menu.")
    else:
        print(f"Partial installation: {success_count}/{len(IMAGE_EXTENSIONS)} extensions")

    print()
    print("To uninstall, run: image-alt-text-uninstall")


def uninstall():
    """Remove the Windows context menu integration."""
    print("Image Alt Text Generator - Uninstaller")
    print("=" * 45)
    print()
    print("Removing context menu entries...")
    print()

    success_count = 0
    for ext in IMAGE_EXTENSIONS:
        if uninstall_for_extension(ext):
            print(f"  [OK] {ext}")
            success_count += 1
        else:
            print(f"  [FAIL] {ext}")

    print()
    print("Uninstallation complete!")
    print()
    print("To reinstall, run: image-alt-text-install")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall()
    else:
        install()
