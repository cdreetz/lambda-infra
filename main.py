import os
import time
import requests
import paramiko
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()


class LambdaLabsManager:
    BASE_URL = "https://cloud.lambdalabs.com/api/v1"

    def __init__(self, api_key: str, ssh_key_path: str):
        self.api_key = api_key
        self.ssh_key_path = ssh_key_path
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

    def create_instance(self, region_name: str, instance_type_name: str, ssh_key_name: str, name: str = None) -> str:
        """Create a new instance."""
        data = {
            "region_name": region_name,
            "instance_type_name": instance_type_name,
            "ssh_key_names": [ssh_key_name],
            "quantity": 1
        }
        if name:
            data["name"] = name

        response = self._make_request("POST", "instance-operations/launch", data)
        return response['data']['instance_ids'][0]

    def get_instance_details(self, instance_id: str) -> Dict[str, Any]:
        """Get details of a specific instance."""
        return self._make_request("GET", f"instances/{instance_id}")

    def get_running_insances(self) -> List[Dict[str, Any]]:
        """Get a list of all currently running instances"""
        response = self._make_request("GET", "instances")
        return response['data']

    def wait_for_instance_ready(self, instance_id: str, timeout: int = 600) -> Dict[str, Any]:
        """Wait for an instance to become active."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            instance = self.get_instance_details(instance_id)['data']
            if instance['status'] == 'active':
                return instance
            time.sleep(10)
        raise TimeoutError("Instance did not become active within the specified timeout.")

    def run_training_code(self, instance_id: str, script_path: str, remote_path: str = '/home/ubuntu') -> None:
        """Run training code on a specific instance."""
        instance = self.get_instance_details(instance_id)['data']
        ip_address = instance['ip']

        # Setup SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            # Load the private key
            private_key = paramiko.RSAKey.from_private_key_file(self.ssh_key_path)

            # Connect using the private key
            ssh.connect(ip_address, username='ubuntu', pkey=private_key)

            # Upload the script
            sftp = ssh.open_sftp()
            remote_script_path = os.path.join(remote_path, os.path.basename(script_path))
            sftp.put(script_path, remote_script_path)
            sftp.close()

            # Run the script
            stdin, stdout, stderr = ssh.exec_command(f"python {remote_script_path}")
            print(stdout.read().decode())
            print(stderr.read().decode())

        except Exception as e:
            print(f"An error occurred: {str(e)}")

        finally:
            ssh.close()

    def destroy_instance(self, instance_id: str) -> None:
        """Destroy a specific instance."""
        data = {"instance_ids": [instance_id]}
        self._make_request("POST", "instance-operations/terminate", data)




def main():
    api_key = os.getenv("LAMBDA_API_KEY")
    if not api_key:
        raise ValueError("Please set the LAMBDA_API_KEY env variable")

    manager = LambdaLabsManager(api_key)

    #available_instances = manager.get_available_instances()
    #print("Available instances")
    #for instance in available_instances:
    #    print(instance)

    #instance_id = manager.create_instance("us-east-1", "gpu_1x_a10", "pc", "training-instance")
    #print(f"Created instance: {instance_id}")

    #instance = manager.wait_for_instance_ready(instance_id)
    #print(f"Instance is ready: {instance}")

    current_instances = manager.get_running_insances()
    print("Current running instances")
    print(current_instances)

    res = manager.run_training_code(current_instances[0]['id'], "./test_train.py")
    print(res)


if __name__ == "__main__":
    main()