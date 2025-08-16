import re
import time
import openai
from utils.db import get_db_connection as get_db

def generate_mcq_questions(role_name, desired_count=15, max_attempts=3):
    all_questions = []

    for attempt in range(max_attempts):
        prompt = f"""
        Generate {desired_count} multiple choice questions for the job role "{role_name}". 
        Provide each question with 4 options labeled A, B, C, D and specify the correct answer.
        Format the output exactly like this:

        Q1: Question text?
        A) option1
        B) option2
        C) option3
        D) option4
        Answer: B
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.7
            )

            text = response.choices[0].message.content

            pattern = re.compile(
                r"Q\d+:\s*(.+?)\n"
                r"A\)\s*(.+?)\n"
                r"B\)\s*(.+?)\n"
                r"C\)\s*(.+?)\n"
                r"D\)\s*(.+?)\n"
                r"Answer:\s*([ABCD])",
                re.DOTALL
            )

            matches = pattern.findall(text)

            for match in matches:
                all_questions.append({
                    "question": match[0].strip(),
                    "option_a": match[1].strip(),
                    "option_b": match[2].strip(),
                    "option_c": match[3].strip(),
                    "option_d": match[4].strip(),
                    "correct_answer": match[5].strip()
                })

            if len(all_questions) >= desired_count:
                return all_questions[:desired_count]

            time.sleep(2)

        except Exception as e:
            print(f"[Error] GPT request failed on attempt {attempt+1}: {e}")
            time.sleep(2)

    return all_questions[:desired_count]
