import os
import json
import google.generativeai as genai

def get_ai_suggestion(dom_content, failed_locator, exception, selector_preferences):
    """
    Analyzes the DOM with an AI model to suggest new locators.

    NOTE: This function requires a configured Gemini API key.
    For now, it returns a mocked response.
    """
    api_key = "AIzaSyAVV4km7_BIMZB3Lw9xD73tfwglvg_aio4" # os.environ.get("GEMINI_API_KEY")
    if not api_key:
        # --- MOCKED RESPONSE FOR DEVELOPMENT ---
        print("GEMINI_API_KEY not found. Returning a mocked AI response.")
        mock_response = {
            "candidates": [
                {"locator": ("id", "submit-button"), "confidence": 0.95, "rationale": "The ID 'submit-button' is unique and stable."},
                {"locator": ("css", "button[data-testid='submit-form']"), "confidence": 0.9, "rationale": "The data-testid  attribute is designed for testing and is reliable."},
                {"locator": ("xpath", "//button[text()='Submit']"), "confidence": 0.7, "rationale": "XPath based on text is less preferred but available as a fallback."}
            ]
        }
        return mock_response
        # --- END OF MOCKED RESPONSE ---

    # Actual API call to Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-pro')

    prompt = f"""
    As an expert test automation engineer, your task is to repair a broken Selenium locator.
    Analyze the provided HTML and suggest stable, unique, and reliable replacement locators.

    Context:
    - Broken Locator: {failed_locator}
    - Exception Type: {exception}
    - Selector Priority Order: {selector_preferences}

    HTML Content:
    `html
    {dom_content}

`

    Instructions:
    1. Analyze the HTML to find the element that the broken locator was likely targeting.
    2. Generate up to 3 new locator candidates for this element.
    3. For each candidate, provide the locator as a tuple (e.g., ("id", "some-id")), a confidence score (0.0 to 1.0), and a brief
rationale.
    4. Prioritize locators based on the given selector priority order.
    5. Return the output as a JSON object with a single key "candidates", which is a list of suggestion objects. Example:
        {{"candidates": [{{"locator": ["id", "new-id"], "confidence": 0.9, "rationale": "A stable ID."}}]}}
    """

    try:
        response = model.generate_content(prompt)
        # Clean up the response from markdown code blocks if present
        cleaned_response = response.text.strip().replace("`json", "").replace("`", "")
        return json.loads(cleaned_response)
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        return {"candidates": []}