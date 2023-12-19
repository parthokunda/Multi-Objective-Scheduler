import subprocess
import requests


def run_shell_command(command):
    try:
        # Run the shell command and capture its output
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, shell=True)

        # Check if the command was successful (return code 0)
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # If there was an error, print the error message
            print(f"Error: {result.stderr.strip()}")
            return None

    except Exception as e:
        print(f"Exception: {str(e)}")
        return None




def queryProm(query: str) :
    ip = run_shell_command("kubectl  get svc -A | grep prometheus | grep 9090 | awk '{print $4 \":\" $6}'")
    ip = ip.split('/')[0]
    url = f'http://{ip}/api/v1/query'
    params = {
        'query': f'{query}'
    }
    response = requests.get(url, params)
    if response.status_code == 200 :
        return response.json()
    else:
        print('error in query '+query)
        return None

# queryProm('istio_request_bytes_sum{source_app="frontend", destination_app="cartservice"}')