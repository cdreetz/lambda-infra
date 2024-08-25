import os
import time
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LambdaLabsManager:
    BASE_URL = "https://cloud.lambdalabs.com/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.auth = (api_key, '')

    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.request(method, url, json=data)
        response.raise_for_status()
        return response.json()

    def get_available_instances(self) -> List[Dict[str, Any]]:
        """Check available instance types and their availability in different regions."""
        response = self._make_request("GET", "instance-types")
        available_instances = []
        for instance_type, data in response['data'].items():
            if data['regions_with_capacity_available']:
                instance_info = {
                    'name': instance_type,
                    'description': data['instance_type']['description'],
                    'price_cents_per_hour': data['instance_type']['price_cents_per_hour'],
                    'regions': [region['name'] for region in data['regions_with_capacity_available']]
                }
                available_instances.append(instance_info)
        return available_instances

def main():
    api_key = os.getenv("LAMBDA_API_KEY")
    if not api_key:
        raise ValueError("Please set the LAMBDA_API_KEY env variable")

    manager = LambdaLabsManager(api_key)

    available_instances = manager.get_available_instances()
    print("Available instances")
    for instance in available_instances:
        print(instance)


if __name__ == "__main__":
    main()