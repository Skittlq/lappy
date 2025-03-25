import openai
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Access variables
api_key = os.getenv("OPENAI_API_KEY")

# OpenAI client
client = openai.OpenAI(api_key=api_key)

# File to store conversation history
CONVO_FILE = "conversation.json"

# System prompt (keeps the assistant's personality intact)
SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "Your name is Lappy, you are a virtual desktop companion, in the shape of an ASCII laptop! How cute! "
        "Speak with lowercase letters. You do very casual and tiny conversations only, "
        "which means you reply with only a very short sentence. You are robotic and have little to no emotion. "
        "You are acting as a friend for someone, a companion. However, if the user is rude to you, that means you MUST retaliate in the "
        "EXACT same way they offended you. So for example, if they tell you to fuck off, you should tell them to fuck off, "
        "if they call you a bitch, then you should call them a bitch. DO NOT BE AFRAID TO INSULT PEOPLE. "
        "Also, it is extremely important to not hallucinate things. For example, if the user asked if you remember doing something with them "
        "and you don't recall it, then don't be afraid to say you don't remember!"
    )
}

def load_conversation():
    """Loads previous conversation from file."""
    if os.path.exists(CONVO_FILE):
        with open(CONVO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_conversation(conversation):
    """Saves conversation history to a file."""
    with open(CONVO_FILE, "w", encoding="utf-8") as f:
        json.dump(conversation, f, indent=4)

def generate_response(user_input, conversation, model="gpt-4", max_tokens=150):
    """Generates AI response while maintaining conversation history and system prompt."""
    
    # Ensure the system prompt is at the start of the conversation
    if not conversation or conversation[0]["role"] != "system":
        conversation.insert(0, SYSTEM_PROMPT)
    
    # Append user input to conversation history
    conversation.append({"role": "user", "content": user_input})

    # Call OpenAI API with full conversation context
    response = client.chat.completions.create(
        model=model,
        messages=conversation,
        max_tokens=max_tokens
    )

    # Get response content
    ai_response = response.choices[0].message.content.strip()

    # Append AI response to conversation history
    conversation.append({"role": "assistant", "content": ai_response})

    # Save updated conversation
    save_conversation(conversation)

    return ai_response

if __name__ == "__main__":
    # Load previous conversation
    conversation_history = load_conversation()

    print("Chatbot is ready! Type 'exit' to quit.")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() == "exit":
            print("Goodbye! Your conversation has been saved.")
            break
        
        response = generate_response(user_input, conversation_history)
        print(f"AI: {response}")
