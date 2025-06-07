from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from llama_cpp import Llama
import os

app = FastAPI()

MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/phi-3.gguf')
llm = None
@app.get("/")
def read_root():
    return {"message": "Hello, FastAPI with llama.cpp!"}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run inference with Phi-3 GGUF using llama.cpp")
    parser.add_argument("--max_tokens", type=int, default=10000000000 , help="Maximum tokens to generate")
    parser.add_argument("--temperature", type=float, default=0.7, help="Sampling temperature")
    args = parser.parse_args()

    # Load system prompt
    prompt_path = os.path.join(os.path.dirname(__file__), '../prompt.txt')
    if not os.path.exists(MODEL_PATH):
        print(f"Model file not found at {MODEL_PATH}")
        exit(1)
    if not os.path.exists(prompt_path):
        print(f"Prompt file not found at {prompt_path}")
        exit(1)
    with open(prompt_path, 'r') as f:
        system_prompt = f.read().strip()

    llm = Llama(model_path=MODEL_PATH)
    print("Welcome to DebateLab CLI! Type 'exit' to quit.")
    chat_history = []
    while True:
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        chat_history.append({"role": "user", "content": user_input})
        # Build the full prompt
        full_prompt = system_prompt + "\n"
        for turn in chat_history:
            if turn["role"] == "user":
                full_prompt += f"User: {turn['content']}\n"
            else:
                full_prompt += f"Debater: {turn['content']}\n"
        full_prompt += "Debater:"
        output = llm(
            full_prompt,
            max_tokens=args.max_tokens,
            temperature=args.temperature
        )
        response = output["choices"][0]["text"].strip()
        print(f"Debater: {response}")
        chat_history.append({"role": "debater", "content": response})
