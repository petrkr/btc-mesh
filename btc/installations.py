import subprocess, os, sys

def is_user_in_group(username, groupname):
    try:
        # Use the "groups" command to check group membership
        groups_output = subprocess.check_output(["groups", username], universal_newlines=True)
        return groupname in groups_output
    except subprocess.CalledProcessError:
        return False

def add_user_to_group(username, groupname):
    try:
        # Use the "usermod" command to add the user to the group
        subprocess.check_call(["sudo", "usermod", "-aG", groupname, username])
        print(f"User {username} has been added to the {groupname} group.")
    except subprocess.CalledProcessError:
        print(f"Failed to add {username} to the {groupname} group.")


# Check if the current user is in the 'dialout' group
current_user = os.getlogin()
group_name = "dialout"

if is_user_in_group(current_user, group_name):
    print(f"User {current_user} is already a member of the {group_name} group.")
else:
    add_user_to_group(current_user, group_name)


def install_meshtastic():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'meshtastic'])
        print("meshtastic has been successfully installed.")
    except subprocess.CalledProcessError:
        print("Failed to install meshtastic. Please install it manually.")
    except Exception as e:
        print(f"An error occurred during installation: {e}")

try:
    # Attempt to import the 'meshtastic' module
    import meshtastic

    print("meshtastic is already installed.")
except ImportError:
    # 'meshtastic' is not installed; install it using pip
    print("Installing meshtastic...")
    install_meshtastic()


def install_bdkpython():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'bdkpython'])
        print("bdkpython has been successfully installed.")
    except subprocess.CalledProcessError:
        print("Failed to install bdkpython. Please install it manually.")
    except Exception as e:
        print(f"An error occurred during installation: {e}")

try:
    # Attempt to import the 'bdkpython' module
    import bdkpython

    print("bdkpython is already installed.")
except ImportError:
    # 'bdkpython' is not installed; install it using pip
    print("Installing bdkpython...")
    install_bdkpython()

def install_pandas_dataframe():
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas'])
        print("pandas.dataframe has been successfully installed.")
    except subprocess.CalledProcessError:
        print("Failed to install pandas.dataframe. Please install it manually.")
    except Exception as e:
        print(f"An error occurred during installation: {e}")


# Check if pandas.dataframe is already installed
try:
    import pandas as pd
    # print("pandas.dataframe is already installed.")
except ImportError:
    print("Installing pandas.dataframe...")
    install_pandas_dataframe()


