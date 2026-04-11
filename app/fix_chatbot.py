import re

with open('chatbot.py', 'r') as f:
    content = f.read()

old = '''def get_gemini_response(messages, emotion, confidence, api_key, max_tokens, temperature):
    try:
        genai.configure(api_key=api_key)
        gemini = genai.GenerativeModel('gemini-2.5-flash')'''

new = '''def get_gemini_response(messages, emotion, confidence, api_key, max_tokens, temperature):
    try:
        client = genai.Client(api_key=api_key)'''

content = content.replace(old, new)

old2 = '''        chat = gemini.start_chat(history=history)
        full_prompt = f"{system_prompt}\\n\\nUser: {messages[-1]['content']}"
        response = chat.send_message(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            )
        )
        return response.text'''

new2 = '''        full_prompt = system_prompt + "\\n\\nConversation history:\\n"
        for msg in messages[:-1]:
            role = "User" if msg['role'] == 'user' else "EmotiBot"
            full_prompt += f"{role}: {msg['content']}\\n"
        full_prompt += f"\\nUser: {messages[-1]['content']}"
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=full_prompt
        )
        return response.text'''

content = content.replace(old2, new2)

with open('chatbot.py', 'w') as f:
    f.write(content)

print("Done!")
