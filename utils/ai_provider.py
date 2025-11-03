import os
import re
import sys
import json
import logging
import google.generativeai as genai
import anthropic
from utils.config_loader import load_config

# Configure the logger
logger = logging.getLogger(__name__)
config = load_config()


def _load_prompt_template():
      """Loads the self-healing prompt from the markdown file."""
      try:
          prompt_path = os.path.join(config["prompt_dir"], "self_healing.md")
          with open(prompt_path, "r", encoding="utf-8") as f:
              return f.read()
      except FileNotFoundError:
          logger.error(f"Prompt template file not found at {prompt_path}")
          return None
      except Exception as e:
          logger.error(f"Failed to load prompt template: {e}")
          return None


def _get_gemini_suggestion(prompt, config):
    """Gets locator suggestions from Google Gemini."""
    gemini_config = config.get("gemini", {})
    api_key = gemini_config.get("api_key")
    model_name = gemini_config.get("model")


    if not api_key or not model_name:
        logger.error("Gemini API key or model name is not configured in config.json.")
        return None
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(model_name)

    logger.info(f"Sending request to Gemini API ({model_name})...")
    response = model.generate_content(prompt)

    cleaned_response = re.search(r'```json\n({.*?})\n```', response.text, re.DOTALL)
    if not cleaned_response:
        logger.error(f"Gemini response was not in the expected JSON format. Raw response: {response.text}")
        return None
    return json.loads(cleaned_response.group(1))


def _get_anthropic_suggestion(prompt, config):
    """Gets locator suggestions from Anthropic Claude."""
    anthropic_config = config.get("anthropic", {})
    api_key = anthropic_config.get("api_key")
    model_name = anthropic_config.get("model")


    if not api_key or not model_name:
        logger.error("Anthropic API key or model name is not configured in config.json.")
        return None


    try:
        client = anthropic.Anthropic(api_key=api_key.strip())

        logger.info(f"Sending request to Anthropic API ({model_name})...")
        message = client.messages.create(
            model=model_name,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text
        cleaned_response = re.search(r'```json\n({.*?})\n```', response_text, re.DOTALL)
        if not cleaned_response:
            logger.error(f"Anthropic response was not in the expected JSON format. Raw response: {response_text}")
            return None
        return json.loads(cleaned_response.group(1))
    except Exception as e:
        logger.error(f"Failed to get locator suggestions from Anthropic: {e}")
        return None


def get_ai_suggestion(dom_content, original_locator, exception_type, selector_preferences):
    """
    Gets AI-powered locator suggestions from the configured provider.
    This function acts as a dispatcher.
    """
    config = load_config()
    provider = config.get("ai_provider", "anthropic")


    prompt_template = _load_prompt_template()
    if not prompt_template:
        return None

    prompt = prompt_template.format(
        dom_content=dom_content,
        failed_locator=original_locator,
        exception_type=exception_type,
        selector_preferences=selector_preferences
    )


    try:
        if provider == "anthropic":
            return _get_anthropic_suggestion(prompt, config)
        elif provider == "gemini":
            return _get_gemini_suggestion(prompt, config)
        else:
            logger.error(f"AI provider '{provider}' is not supported. Please use 'gemini' or 'anthropic'.")
            return None

    except Exception as e:
        logger.error(f"An error occurred while communicating with the {provider} API: {e}")
        return None
