from config.metadata import (
    APP_NAME,
    APP_TAGLINE,
    AUTHOR,
    CONTACT_EMAILS,
    ETHICAL_NOTICE,
    REPO_URL,
    VERSION,
)
from ui.colors import CYAN, GREEN, RESET, YELLOW


def show_banner():
    contacts = ", ".join(CONTACT_EMAILS)
    print(
        fr"""
    _   __                ____                       __             
   / | / /_  ______ ___  / __ )________  ____ ______/ /_  ___  _____
  /  |/ / / / / __ `__ \/ __  / ___/ _ \/ __ `/ ___/ __ \/ _ \/ ___/
 / /|  / /_/ / / / / / / /_/ / /  /  __/ /_/ / /__/ / / /  __/ /    
/_/ |_/\__,_/_/ /_/ /_/_____/_/   \___/\__,_/\___/_/ /_/\___/_/     

{CYAN}    {APP_TAGLINE} - {APP_NAME}{RESET}
{GREEN}    * Version: {VERSION}{RESET}
{GREEN}    * Author: {AUTHOR}{RESET}
{YELLOW}    * Contact: {contacts}{RESET}
{YELLOW}    * Repo: {REPO_URL}{RESET}
{CYAN}    * {ETHICAL_NOTICE}{RESET}
"""
    )
