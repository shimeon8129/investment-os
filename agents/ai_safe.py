from agents.gpt_agent import call_gpt

def call_ai_safe(prompt):

    try:
        result = call_gpt(prompt)

        # 基本驗證
        if not isinstance(result, dict):
            raise ValueError("Invalid format")

        if "topic" not in result:
            raise ValueError("Missing topic")

        return result

    except Exception as e:
        print("⚠️ AI failed, fallback to mock:", e)

        # fallback mock（保底）
        return {
            "topic": "Other",
            "sentiment": "neutral",
            "strength": 50,
            "summary": "fallback"
        }

