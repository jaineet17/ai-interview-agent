#!/usr/bin/env python3
import requests
import sys

def test_ollama_connection(model="llama2"):
    print(f"Testing connection to Ollama with model: {model}")
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": "Say 'Hello from Ollama!' if you can read this.",
                "stream": False
            },
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "")
            print(f"Success! Response: {result}")
            return True
        else:
            print(f"Error: Received status code {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"Error connecting to Ollama: {str(e)}")
        print("\nIs Ollama running? Please start it and try again.")
        return False

if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "llama2"
    success = test_ollama_connection(model)
    if not success:
        print("\nTroubleshooting tips:")
        print("1. Make sure Ollama is installed and running")
        print("2. Verify the model is downloaded with 'ollama list'")
        print("3. If not, download it with 'ollama pull llama2'")
        print("4. Try again with './test_ollama.py'")
    sys.exit(0 if success else 1) 