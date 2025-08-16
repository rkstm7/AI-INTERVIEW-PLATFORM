import openai

def evaluate_answer_ai(question, user_answer):
    prompt = f"Question: {question}\nUser Answer: {user_answer}\nCorrect or Incorrect? Answer with 'Correct' or 'Incorrect'."
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=20,
            temperature=0
        )
        result = response.choices[0].message.content.strip()
        return result.lower() == "correct"
    except Exception as e:
        print(f"[AI Evaluation Error]: {e}")
        return False
