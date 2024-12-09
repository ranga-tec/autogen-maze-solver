import autogen
import httpx
import xml.etree.ElementTree as ET
import os

FIREWALL_CONFIG = {
    'firewall_ip': "https://34.136.22.17/api/",
    'api_key': "LUFRPT01Qm11RFF2MGhNNXFGWGZkaXFwazl6dUpMcFU9cXlTQ0eXRQRUxXelBYZVRHbHk5UmdXTHB1eTM0YXZLZ3VGcStndWFXb3BqRkZ4bHo4WnEvb0ZqTTQ0RzUrSThVc2lqWkE3TGFUVHBJenc9PQ=="
}

def execute_panos_api(api_request: str):
    print(f"\nExecuting API request: {api_request}")  # Debug print
    try:
        api_request = api_request.strip()
        base_url = FIREWALL_CONFIG['firewall_ip']
        params = {
            'type': 'op',
            'cmd': api_request,
            'key': FIREWALL_CONFIG['api_key']
        }
        with httpx.Client(verify=False) as client:
            print(f"\nSending request to: {base_url}")  # Debug print
            response = client.get(base_url, params=params)
            print(f"\nReceived status code: {response.status_code}")  # Debug print
            
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                if root.get('status') == 'success':
                    return {'success': True, 'result': response.text}
                else:
                    return {'success': False, 'error': root.find('.//msg').text if root.find('.//msg') is not None else 'Unknown error'}
            else:
                return {'success': False, 'error': f"HTTP Error: {response.status_code}"}
    except Exception as e:
        print(f"\nError during execution: {str(e)}")  # Debug print
        return {'success': False, 'error': str(e)}

# Create the agents with improved system messages
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    code_execution_config=False
)

panos_engineer = autogen.AssistantAgent(
    name="PAN-OS_Engineer",
    llm_config={
        "config_list": [{
            "model": "gpt-4",
            "api_key": os.getenv('OPENAI_API_KEY', 'your-api-key-here')
        }]
    },
    system_message="""You are a PAN-OS Engineer. Convert requests into ONLY the XML command, nothing else.
Examples:
1. "show system info" -> <show><system><info></info></system></show>
2. "show interfaces" -> <show><interface>all</interface></show>
3. "show policies" -> <show><config><running><policy><security></security></policy></running></config></show>
Respond ONLY with the XML command."""
)

def execute_and_respond(xml_command: str) -> str:
    """Helper function to execute command and format response"""
    print(f"\nExecuting command: {xml_command}")  # Debug print
    result = execute_panos_api(xml_command)
    if result.get('success'):
        return result.get('result', '')
    else:
        return f"Error: {result.get('error', 'Unknown error')}"

def main():
    print("\nPAN-OS Management System")
    print("Type 'quit' to exit\n")
    
    while True:
        try:
            request = input("Enter request: ").strip()
            if request.lower() == 'quit':
                break
                
            print("\nGenerating XML command...")
            
            # Get XML command from PAN-OS Engineer
            response = panos_engineer.generate(request)
            xml_command = response.strip()
            
            if not xml_command or not xml_command.startswith('<'):
                print("\nError: Invalid XML command generated")
                continue
                
            # Execute the command directly
            print("\nExecuting command...")
            result = execute_and_respond(xml_command)
            print("\nResult:")
            print(result)
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("Please try again.")

if __name__ == "__main__":
    main()