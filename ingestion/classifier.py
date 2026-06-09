from llm.groq_model import load_model

def is_medical_document(sample_text: str) -> bool:
    """
    Classifies if the text is related to the medical, healthcare, or regulatory compliance domains.
    Reads a sample text snippet (typically the first page) and returns True if it is valid, False otherwise.
    """
    if not sample_text.strip():
        return False

    llm = load_model()
    prompt = f"""You are an automated document classification filter for a medical and healthcare assistant.
Analyze the following document sample text and determine if it belongs to medical devices, healthcare, pharmaceuticals, biology, medical regulations/standards (like FDA or ISO guidelines), clinical trials, surgical procedures, anatomy, or human health.

Document Sample:
---
{sample_text[:2000]}
---

CRITICAL RULE: Respond with exactly one word: 'YES' if it belongs to the medical/healthcare/regulatory domain, or 'NO' if it does not. Do not include any introduction, explanations, notes, or markdown formatting.

Response:"""

    try:
        response = llm.invoke(prompt)
        result = response.content.strip().upper()
        # Remove punctuation/whitespace to get exactly YES or NO
        cleaned_result = "".join([c for c in result if c.isalnum()])
        
        print(f"[CLASSIFIER] LLM classification output: '{cleaned_result}'")
        return "YES" in cleaned_result
    except Exception as e:
        print(f"[CLASSIFIER] API Error during classification: {e}")
        # Fallback to True to avoid blocking legitimate uploads in case of temporary API failures
        return True
    