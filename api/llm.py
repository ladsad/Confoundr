import os
from groq import Groq

# Initialize Groq client only if API key is present
api_key = os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key) if api_key else None

def generate_explanation(check_name: str, explanation: str, evidence: dict) -> str:
    """
    Calls the Groq LLM to generate a plain-language explanation and suggested fix for a failed causal check.
    """
    if not client:
        return "AI insights are disabled because GROQ_API_KEY is not set."

    prompt = f"""
    You are an expert causal inference statistician helping a data scientist debug their dataset.
    
    A causal validity check has failed.
    - Check Name: {check_name}
    - Technical Explanation: {explanation}
    - Statistical Evidence: {evidence}
    
    Please provide:
    1. A short, plain-language explanation of what this failure means for their causal model.
    2. A practical, actionable suggestion on how to fix the dataset to resolve this issue.
    
    Keep it extremely concise, professional, and do not use generic filler words.
    """

    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama3-8b-8192",
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI insight generation failed: {str(e)}"
