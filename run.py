import threading
import subprocess
import os
from dotenv import load_dotenv
import shutil
import json
from datetime import datetime

RED = '\033[31m'
GREEN = '\033[32m'
BLUE = '\033[34m'
RESET = '\033[0m'


def run_discord_bot():
    subprocess.run(["python3", "./discord-bot/main.py"])

def run_flask_app():
    subprocess.run(["python3", "./web-dashboard/app.py"])
    
def check_requirements_installed():
    try:
        subprocess.run(["pip", "check"], check=True)
        print(f"{GREEN}All requirements from requirements.txt are installed.{RESET}")
    except subprocess.CalledProcessError:
        print(f"{RED}Some requirements are not installed. Please check.{RESET}")
        exit()
        
def check_env_variable(env_file, var):
    if os.path.exists(env_file):
        with open(env_file) as f:
            env_content = f.readlines()
            for line in env_content:
                if line.startswith(var + '='):
                    value = line.split('=', 1)[1].strip()  # Split only on the first '='
                    if value:
                        print(f"{GREEN}{var} is present in {env_file} and is not empty.{RESET}")
                    else:
                        print(f"{RED}{var} is missing or empty in {env_file}.{RESET}")
                        exit()
                    return
            print(f"{RED}{var} is missing in {env_file}.{RESET}")
            exit()
    else:
        print(f"{RED}{env_file} file does not exist.{RESET}")
        exit()

def check_valid_port(port):
    """Check if the given port is a valid port number."""
    try:
        # Attempt to convert to an integer
        port = int(port)
    except ValueError:
        print(f"{RED}{port} is not a valid port number (not an integer){RESET}")
        exit()

    if 0 <= port <= 65535:
        print(f"{GREEN}{port} is a valid port (not sure if it's available or not){RESET}")
        return True
    else:
        print(f"{RED}{port} is not a valid port number (out of range){RESET}")
        exit()

def check_file_exists(file_path):
    if os.path.exists(file_path):
        print(f"{GREEN}{file_path} exists.{RESET}")
    else:
        print(f"{RED}{file_path} does not exist.{RESET}")
        exit()
 
def copy_env_file():
    """Copy .env.example to .env."""
    source = './.env.example'
    destination = './.env'

    if os.path.exists(source):
        shutil.copyfile(source, destination)
        print(f"{RED}The app generate ./.env file, please fill it with the required variables and start the app agian.{RESET}")
    else:
        print(f"{source} does not exist.")

def check_env_exists():
    if os.path.exists('./.env'):
        print(f"{GREEN}./.env file exists.{RESET}")
    else:
        print(f"{RED}./.env file does not exist.{RESET}")
        copy_env_file()
        exit()

expected_structure = {
    "log_category_id": None,
    "deleted_messages_channel_id": None,
    "edited_messages_channel_id": None,
    "voice_activity_channel_id": None,
    "guild_activity_channel_id": None,
    "members_activity_channel_id": None
}


def is_valid_log_channels_json(data):
    if isinstance(data, dict):
        return all(key in data for key in expected_structure)
    return False

def create_log_channels_json():
    try:
        with open('./discord-bot/log_channels.json', 'w') as file:
            json.dump(expected_structure, file, indent=4)
    except:
        print(f"{RED}wtf, file not exists")
        exit()


def backup_invalid_file(filepath):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file_path = f'{os.path.splitext(filepath)[0]}_backup_{timestamp}{os.path.splitext(filepath)[1]}'
    shutil.copyfile(filepath, backup_file_path)
    print(f"{BLUE}Copied invalid file to {backup_file_path}.{RESET}")

if __name__ == "__main__":
        
    print("""
o.OOOo.                                    o        o                                     
 O    `o  o                               O        O                                      
 o      O                                 o        o                                      
 O      o                                 o        o                                      
 o      O O  .oOo  .oOo  .oOo. `OoOo. .oOoO        O       .oOo. .oOoO .oOoO .oOo. `OoOo. 
 O      o o  `Ooo. O     O   o  o     o   O        O       O   o o   O o   O OooO'  o     
 o    .O' O      O o     o   O  O     O   o        o     . o   O O   o O   o O      O     
 OooOO'   o' `OoO' `OoO' `OoO'  o     `OoO'o       OOoOooO `OoO' `OoOo `OoOo `OoO'  o     
                                                                     O     O              
                                                                  OoO'  OoO'              
          """)
    print("\nThanks for downloadin the app!")
    print("Checking if everything is ready...")
    
    check_requirements_installed()
    
    check_env_exists()
    
    check_env_variable("./.env", "BOT_TOKEN")
    check_env_variable("./.env", "DASHBOARD_PORT")
    check_env_variable("./.env", "LOG_TO_DISCORD")

    load_dotenv()
    check_valid_port(os.getenv("DASHBOARD_PORT"))
    check_file_exists('./web-dashboard/app.py')
    check_file_exists('./discord-bot/main.py')
    
    # Checking for log_channels.json
    if os.path.exists('./discord-bot/log_channels.json'):
        # If yes, make sure it's valid
        with open('./discord-bot/log_channels.json', 'r') as file:
            try:
                # Load the JSON data
                data = json.load(file)
                # Validate the JSON structure
                if not is_valid_log_channels_json(data):
                    print(f"{RED}Invalid ./discord-bot/log_channels.json structure.{RESET}")
                    backup_invalid_file('./discord-bot/log_channels.json')
                    create_log_channels_json()
                    print(f"{GREEN}Created a new ./discord-bot/log_channels.json.{RESET}")
            except json.JSONDecodeError:
                print(f"{RED}./discord-bot/log_channels.json is invalid.{RESET}")
                backup_invalid_file('./discord-bot/log_channels.json')
                create_log_channels_json()
                print(f"{GREEN}Created a new ./discord-bot/log_channels.json.{RESET}")
    else:
        print(f"{RED}./discord-bot/log_channels.json does not exists, creating a default one...")
        create_log_channels_json()
        print(f"{GREEN}Created a new ./discord-bot/log_channels.json.{RESET}")
    check_file_exists('./discord-bot/log_channels.json')        
    

    
    print("\nEverything looks good! Starting the app now...")
    print(f"You can access the web dashboard on http://127.0.0.1:{os.getenv("DASHBOARD_PORT")}\n\n")
    print("==== START OF APPLICATION LOGS ====")
    discord_thread = threading.Thread(target=run_discord_bot)
    flask_thread = threading.Thread(target=run_flask_app)

    #discord_thread.start()
    flask_thread.start()

    #discord_thread.join()
    flask_thread.join()
    