import requests
import os
import urllib3
import time

import requests.cookies

class UNASPro:
    def __init__(self, hostname: str, username: str, password: str):
        self.hostname = f'https://{hostname}'
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.logged_in = False

        urllib3.disable_warnings()

        login_retry_frequency = int(os.getenv("LOGIN_RETRY_FREQUENCY", "10"))

        self.request_timeout = int(os.environ.get("REQUEST_TIMEOUT", "10"))

        login = self.login()
        if not login:
            print(f"Failed to login... trying again every {login_retry_frequency} seconds")
            while not self.logged_in:
                login = self.login()
                if login:
                    print("Logged in!")
                else:
                    print(f"Failed to login... trying again in {login_retry_frequency} seconds")
                    time.sleep(login_retry_frequency)

    def is_logged_in(self):
        return self.logged_in

    def login(self):
        data = {
            "username": self.username,
            "password": self.password,
            "token":"",
            "rememberMe": False
        }
        
        if self.debug:
            print(f"Logging in to {self.hostname} as {self.username}")
        
        try:
            response = self.make_request("POST", f'{self.hostname}/api/auth/login', data)
            if 'deviceToken' in response:
                self.logged_in = True
                return True
        except Exception as e:
            print(f'Error: {e}')
            return False
    
    def get_system_info(self):
        path = 'proxy/drive/api/v1/systems/device-info'
        if self.debug:
            print(f"Getting system info from {self.hostname}")
        try:
            response = self.make_request("GET", f'{self.hostname}/{path}', {})
            return response['data'] if 'data' in response else response
        except Exception as e:
            print(f'Error: {e}')
            return {"error": str(e)}

    def get_latest_firmware(self):
        path = 'api/firmware/update'
        if self.debug:
            print(f"Getting latest firmware info from {self.hostname}")
        try:
            response = self.make_request("GET", f'{self.hostname}/{path}', {})
            major_version = response['version_major']
            minor_version = response['version_minor']
            patch_version = response['version_patch']
            return f"{major_version}.{minor_version}.{patch_version}"
        except Exception as e:
            print(f'Error: {e}')
            return {"error": str(e)}

    def get_storage_info(self):
        path = 'proxy/drive/api/v1/systems/storage?type=detail'
        if self.debug:
            print(f"Getting storage info from {self.hostname}")
        try:
            response = self.make_request("GET", f'{self.hostname}/{path}', {})
            return response['data'] if 'data' in response else response
        except Exception as e:
            print(f'Error: {e}')
            return {"error": str(e)}

    def get_drive_slots(self):
        storage_info = self.get_storage_info()
        if 'error' in storage_info:
            return storage_info
        
        return storage_info['diskInfo']['slots']

    def get_shared_drives(self):
        path = 'proxy/drive/api/v1/shared'
        if self.debug:
            print(f"Getting shared drives from {self.hostname}")
        try:
            response = self.make_request("GET", f'{self.hostname}/{path}', {})
            return response['data'] if 'data' in response else response
        except Exception as e:
            print(f'Error: {e}')
            return {"error": str(e)}
        
    def get_personal_drives(self):
        path = 'proxy/drive/api/v1/systems/storage/personal'
        if self.debug:
            print(f"Getting personal drive from {self.hostname} for {self.username}")
        try:
            response = self.make_request("GET", f'{self.hostname}/{path}', {})
            return response['data'] if 'data' in response else response
        except Exception as e:
            print(f'Error: {e}')
            return {"error": str(e)}
        
    # Returns the total used space on the NAS in bytes
    def get_total_used_space(self):
        personal = self.get_personal_drives()
        shares = self.get_shared_drives()

        if 'error' in personal:
            return personal
        if 'error' in shares:
            return shares
        
        personal_used = sum([share['usage'] for share in personal])
        shared_used = sum([share['usage'] for share in shares])
        return {
            "personal": personal_used,
            "shared": shared_used,
            "total": personal_used + shared_used
        }

    def get_network_interfaces(self):
        device_info = self.get_system_info()
        if 'error' in device_info:
            return device_info
        
        return device_info['networkInterfaces']

    def make_request(self, method: str, url: str, data: dict = None):
        if method == "GET":
            response = self.session.get(url, headers=self.headers, verify=False, timeout=10)
        elif method == "POST":
            response = self.session.post(url, headers=self.headers, json=data, verify=False, timeout=10)
        elif method == "PUT":
            response = self.session.put(url, headers=self.headers, json=data, verify=False, timeout=10)
        elif method == "DELETE":
            response = self.session.delete(url, headers=self.headers, verify=False, timeout=10)
        else:
            return {"error": "Invalid method"}

        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code} {response.reason}"}
