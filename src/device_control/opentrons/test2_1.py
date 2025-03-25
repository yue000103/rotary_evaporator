import requests
import time


# Replace with actual OT2 address
ROBOT_IP_ADDRESS = "127.0.0.1"


def run():
    # POST the protocol and support files to OT2
    response = requests.post(
        url=f"http://{ROBOT_IP_ADDRESS}:31950/protocols",
        headers={"Opentrons-Version": "2"},
        files=[("protocolFile", open("basic_transfer.py", 'rb')),
               ("supportFiles", open("helpers.py", 'rb')),
               ("supportFiles", open("basic_transfer_config.json", 'rb')),
               ]
    )
    print(f"Create Protocol result: {response.json()}")

    # Extract the uploaded protocol id from the response
    protocol_id = response.json()['data']['id']

    try:
        errors = response.json()['data'].get('errors')
        if errors:
            raise RuntimeError(f"Errors in protocol: {errors}")

        run_protocol(protocol_id)

    finally:
        # Use the protocol_id to DELETE the protocol
        requests.delete(
            url=f"http://{ROBOT_IP_ADDRESS}:31950/protocols/{protocol_id}",
            headers={"Opentrons-Version": "2"},
        )


def run_protocol(protocol_id: str):
    # Create a protocol session
    response = requests.post(
        url=f"http://{ROBOT_IP_ADDRESS}:31950/sessions",
        headers={"Opentrons-Version": "2"},
        json={
            "data": {
                "sessionType": "protocol",
                "createParams": {
                    "protocolId": protocol_id
                }
            }
        }
    )
    print(f"Create Session result: {response.json()}")
    # Extract the session id from the response
    session_id = response.json()['data']['id']

    try:
        # Creating the protocol session kicks off a full simulation which can
        # take some time. Wait until session is in the 'loaded' state before running
        while True:
            # Sleep for 1/2 a second
            time.sleep(.5)

            response = requests.get(
                url=f"http://{ROBOT_IP_ADDRESS}:31950/sessions/{session_id}",
                headers={"Opentrons-Version": "2"},
            )

            current_state = response.json()['data']['details']['currentState']
            if current_state == 'loaded':
                break
            elif current_state == 'error':
                raise RuntimeError(f"Error encountered {response.json()}")

        # Send a command to begin a protocol run
        requests.post(
            url=f"http://{ROBOT_IP_ADDRESS}:31950/sessions/{session_id}/commands/execute",
            headers={"Opentrons-Version": "2"},
            json={"data": {"command": "protocol.startRun", "data": {}}}
        )

        # Wait until session is in the 'finished' state
        while True:
            # Sleep for 1/2 a second
            time.sleep(.5)

            response = requests.get(
                url=f"http://{ROBOT_IP_ADDRESS}:31950/sessions/{session_id}",
                headers={"Opentrons-Version": "2"},
            )

            current_state = response.json()['data']['details']['currentState']
            if current_state == 'finished':
                print("Run is complete:")
                print(response.json())
                break
            elif current_state == 'error':
                raise RuntimeError(f"Error encountered {response.json()}")

    finally:
        # Use the session_id to DELETE the session
        requests.delete(
            url=f"http://{ROBOT_IP_ADDRESS}:31950/sessions/{session_id}",
            headers={"Opentrons-Version": "2"},
        )


if __name__ == '__main__':
    run()