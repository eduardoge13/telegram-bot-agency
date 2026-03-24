"""Gemini AI client wrapper."""
from google import genai
from google.genai import types


class GeminiClient:
    """Wraps google-genai SDK to create chat objects with system instructions."""

    def __init__(self, api_key: str):
        """Initialize the Gemini client with the given API key."""
        self._client = genai.Client(api_key=api_key)

    def create_chat(self, system_prompt: str):
        """Create a new Gemini chat object with the given system instruction.

        Returns a Chat object that maintains conversation history automatically.
        Each call to send_message() includes all prior history.
        """
        return self._client.chats.create(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
                temperature=0.7,
            ),
        )
