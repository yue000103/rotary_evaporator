import requests
import json
from datetime import datetime
import time
from src.uilt.yaml_control.setup import get_base_url


class SepuCom:
    def __init__(self):
        """
        Initialize SepuCom with basic API URL.

        Args:
        base_url (str): Basic API URL, e.g., "http://localhost:5000"
        """
        self.base_url = get_base_url("sepu_com")
        self.method_id = 0

    def send_post_request(self, endpoint: str, payload: dict) -> dict:
        """
        Send POST request to specified API endpoint.

        Args:
        endpoint (str): Specific API path, e.g., "/status/init_device"
        payload (dict): Request payload passed as JSON

        Returns:
        dict: Response data from request
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            return response.json()
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "Unable to parse error response JSON content."
            return error_message

    def send_get_request(self, endpoint: str) -> dict:
        """
        Send GET request to specified API endpoint.

        Args:
        endpoint (str): Specific API path, e.g., "/method/only/operate"

        Returns:
        dict: Response data from request
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json()
        else:
            error_message = {
                "status_code": response.status_code,
                "error_message": response.text
            }
            try:
                error_response = response.json()
                error_message["detailed_error"] = json.dumps(error_response, indent=2)
            except ValueError:
                error_message["detailed_error"] = "Unable to parse error response JSON content."
            return error_message