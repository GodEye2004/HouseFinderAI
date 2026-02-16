import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def test_llm():
    token = os.environ.get("GITHUB_TOKEN")
    print(f"Token: {token[:10]}...")
    
    client = OpenAI(
        base_url="https://models.github.ai/inference",
        api_key=token,
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello!"}
            ],
            temperature=0.8,
            max_tokens=10
        )
        print("Success!")
        print(f"Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"Failed! Error: {e}")

if __name__ == "__main__":
    test_llm()
