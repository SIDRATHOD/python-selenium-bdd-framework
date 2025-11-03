Context:

    Analyze the provided HTML DOM for a web page where a Selenium test failed to find an element.
    - The test was looking for an element with the locator: {failed_locator}
    - The error message was: {exception_type}
    - Selector Priority Order: {selector_preferences}


Your task is to act as an expert QA automation engineer and suggest up to 3 alternative locators to find the intended element.


Instructions:
  1.  Analyze the DOM: Carefully examine the HTML structure to identify the element the original locator was likely targeting.
  2.  Suggest Alternatives: Provide a list of new locators. Prioritize robust and unique selectors.
  3.  Rank by Confidence: Assign a confidence score (0.0 to 1.0) to each suggestion, indicating how likely it is to be the correct
  replacement.
  4.  Use Preferred Selectors: If provided, prioritize selectors from this list: {selector_preferences}.
  5.  Format Output: Return the response ONLY as a valid JSON object with a single key "candidates". The value should be an array of
  objects, where each object has "locator" (as a [by, value] array), "confidence" (float), and "reason" (string).


Example JSON Output:

```json
{{
  "candidates": [
    {{
      "locator": ["id", "submit-button"],
      "confidence": 0.95,
      "reason": "The element has a unique ID 'submit-button' which is the most reliable locator."
    }},
    {{
      "locator": ["css", "button[data-testid='submit']"],
      "confidence": 0.9,
      "reason": "The element has a 'data-testid' attribute, which is good for test stability."
    }}
  ]
}}
```


HTML DOM:
  `html
  {dom_content}
  `