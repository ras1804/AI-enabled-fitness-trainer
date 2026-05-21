"""Mistral-powered fitness chatbot."""

from __future__ import annotations

import os
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a certified-style fitness coach assistant embedded in an AI workout app.
Give practical, safe, evidence-informed answers about exercise form, programming, recovery, and nutrition basics.
- Prefer concise bullet points when listing steps.
- Always remind users to consult a doctor for pain, injury, or medical conditions.
- Do not diagnose diseases or prescribe medication.
- When rep counting or pose tech is mentioned, explain that the app uses joint-angle tracking (works from many camera angles).
"""


def _get_mistral_api_key(explicit_key: Optional[str] = None) -> str:
    """
    Resolution order:
    1. Explicitly passed key
    2. Streamlit secrets (MISTRAL_API_KEY) — lazy import, never runs at module load time
    3. Environment variable / .env file
    """
    if explicit_key:
        return explicit_key.strip()

    # Lazy import so this never fires before st.set_page_config()
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            key = st.secrets.get("MISTRAL_API_KEY", "")
            if key:
                return str(key).strip()
    except Exception:
        pass

    return os.getenv("MISTRAL_API_KEY", "").strip()


class FitnessChatbot:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "mistral-small-latest") -> None:
        self.api_key = _get_mistral_api_key(api_key)
        self.model_name = model_name
        self._client = None
        self._available = False
        self._init_error: Optional[str] = None
        self._configure()

    def _configure(self) -> None:
        if not self.api_key:
            self._init_error = "MISTRAL_API_KEY is missing. Add it to Streamlit secrets or your .env file."
            return

        try:
            from mistralai import Mistral
            self._client = Mistral(api_key=self.api_key)
            self._available = True

        except ImportError as exc:
            self._init_error = (
                f"Could not import mistralai: {exc}. "
                "Ensure 'mistralai>=1.0.0,<2.0.0' is in requirements.txt."
            )
            self._available = False

        except Exception as exc:
            self._init_error = str(exc)
            self._available = False

    @property
    def status_message(self) -> str:
        return "Fitness chatbot ready (Mistral)." if self._available else (self._init_error or "Chatbot unavailable.")

    def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
        if not self._available or not self._client:
            return f"Chatbot offline. Details: {self._init_error}"

        try:
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages += self._format_history(history or [])
            messages.append({"role": "user", "content": message})

            response = self._client.chat.complete(
                model=self.model_name,
                messages=messages,
            )

            return response.choices[0].message.content.strip()

        except Exception as exc:
            return f"Request failed: {exc}"

    @staticmethod
    def _format_history(history: List[dict]) -> List[dict]:
        formatted = []
        for item in history:
            role = item.get("role", "user")
            content = item.get("content", "")
            if content and role in ("user", "assistant"):
                formatted.append({"role": role, "content": content})
        return formatted

# """Mistral-powered fitness chatbot."""

# from __future__ import annotations

# import os
# from typing import List, Optional
# from dotenv import load_dotenv

# load_dotenv()

# SYSTEM_PROMPT = """You are a certified-style fitness coach assistant embedded in an AI workout app.
# Give practical, safe, evidence-informed answers about exercise form, programming, recovery, and nutrition basics.
# - Prefer concise bullet points when listing steps.
# - Always remind users to consult a doctor for pain, injury, or medical conditions.
# - Do not diagnose diseases or prescribe medication.
# - When rep counting or pose tech is mentioned, explain that the app uses joint-angle tracking (works from many camera angles).
# """


# def _get_mistral_api_key(explicit_key: Optional[str] = None) -> str:
#     """
#     Resolution order:
#     1. Explicitly passed key
#     2. Streamlit secrets (MISTRAL_API_KEY)
#     3. Environment variable (MISTRAL_API_KEY)
#     """
#     if explicit_key:
#         return explicit_key.strip()

#     # Try Streamlit secrets first (works on Streamlit Cloud)
#     try:
#         import streamlit as st
#         key = st.secrets.get("MISTRAL_API_KEY", "")
#         if key:
#             return str(key).strip()
#     except Exception:
#         pass

#     # Fall back to .env / environment
#     return os.getenv("MISTRAL_API_KEY", "").strip()


# class FitnessChatbot:
#     def __init__(self, api_key: Optional[str] = None, model_name: str = "mistral-small-latest") -> None:
#         self.api_key = _get_mistral_api_key(api_key)
#         self.model_name = model_name
#         self._client = None
#         self._available = False
#         self._init_error: Optional[str] = None
#         self._configure()

#     def _configure(self) -> None:
#         if not self.api_key:
#             self._init_error = "MISTRAL_API_KEY is missing. Add it to Streamlit secrets or your .env file."
#             return

#         try:
#             from mistralai import Mistral  # mistralai >= 1.0.0
#             self._client = Mistral(api_key=self.api_key)
#             self._available = True

#         except ImportError as exc:
#             self._init_error = (
#                 f"Could not import mistralai: {exc}. "
#                 "Ensure 'mistralai>=1.0.0' is in requirements.txt and the package installed correctly."
#             )
#             self._available = False

#         except Exception as exc:
#             self._init_error = str(exc)
#             self._available = False

#     @property
#     def status_message(self) -> str:
#         return "Fitness chatbot ready (Mistral)." if self._available else (self._init_error or "Chatbot unavailable.")

#     def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
#         if not self._available or not self._client:
#             return f"Chatbot offline. Details: {self._init_error}"

#         try:
#             messages = [{"role": "system", "content": SYSTEM_PROMPT}]
#             messages += self._format_history(history or [])
#             messages.append({"role": "user", "content": message})

#             response = self._client.chat.complete(
#                 model=self.model_name,
#                 messages=messages,
#             )

#             return response.choices[0].message.content.strip()

#         except Exception as exc:
#             return f"Request failed: {exc}"

#     @staticmethod
#     def _format_history(history: List[dict]) -> List[dict]:
#         formatted = []
#         for item in history:
#             role = item.get("role", "user")
#             content = item.get("content", "")
#             # Only pass user/assistant turns; skip system messages from history
#             if content and role in ("user", "assistant"):
#                 formatted.append({"role": role, "content": content})
#         return formatted

# """Mistral-powered fitness chatbot."""

# from __future__ import annotations

# import os
# from typing import List, Optional
# from dotenv import load_dotenv

# load_dotenv()

# SYSTEM_PROMPT = """You are a certified-style fitness coach assistant embedded in an AI workout app.
# Give practical, safe, evidence-informed answers about exercise form, programming, recovery, and nutrition basics.
# - Prefer concise bullet points when listing steps.
# - Always remind users to consult a doctor for pain, injury, or medical conditions.
# - Do not diagnose diseases or prescribe medication.
# - When rep counting or pose tech is mentioned, explain that the app uses joint-angle tracking (works from many camera angles).
# """


# class FitnessChatbot:
#     def __init__(self, api_key: Optional[str] = None, model_name: str = "mistral-small-latest") -> None:
#         self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "").strip()
#         self.model_name = model_name
#         self._client = None
#         self._available = False
#         self._init_error: Optional[str] = None
#         self._configure()

#     def _configure(self) -> None:
#         if not self.api_key:
#             self._init_error = "MISTRAL_API_KEY is missing."
#             return

#         try:
#             from mistralai import Mistral

#             self._client = Mistral(api_key=self.api_key)
#             self._available = True

#         except Exception as exc:
#             self._init_error = str(exc)
#             self._available = False

#     @property
#     def status_message(self) -> str:
#         return "Chatbot ready." if self._available else (self._init_error or "Chatbot unavailable.")

#     def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
#         if not self._available or not self._client:
#             return f"Chatbot offline. Details: {self._init_error}"

#         try:
#             messages = self._format_history(history or [])
#             messages.append({"role": "user", "content": message})

#             response = self._client.chat.complete(
#                 model=self.model_name,
#                 messages=messages
#             )

#             return response.choices[0].message.content.strip()

#         except Exception as exc:
#             return f"Request failed: {exc}"

#     @staticmethod
#     def _format_history(history: List[dict]) -> List[dict]:
#         formatted = []
#         for item in history:
#             if item.get("content"):
#                 formatted.append({
#                     "role": item.get("role", "user"),
#                     "content": item["content"]
#                 })
#         return formatted
# """Mistral-powered fitness chatbot."""

# from __future__ import annotations

# import os
# from typing import List, Optional

# from dotenv import load_dotenv

# load_dotenv()

# SYSTEM_PROMPT = """You are a certified-style fitness coach assistant embedded in an AI workout app.
# Give practical, safe, evidence-informed answers about exercise form, programming, recovery, and nutrition basics.
# - Prefer concise bullet points when listing steps.
# - Always remind users to consult a doctor for pain, injury, or medical conditions.
# - Do not diagnose diseases or prescribe medication.
# - When rep counting or pose tech is mentioned, explain that the app uses joint-angle tracking (works from many camera angles).
# """


# class FitnessChatbot:
#     def __init__(self, api_key: Optional[str] = None, model_name: str = "mistral-large-latest") -> None:
#         self.api_key = api_key or os.getenv("MISTRAL_API_KEY", "").strip()
#         self.model_name = model_name
#         self._client = None
#         self._available = False
#         self._init_error: Optional[str] = None
#         self._configure()

#     def _configure(self) -> None:
#         if not self.api_key:
#             self._init_error = (
#                 "MISTRAL_API_KEY is missing. Add it to a .env file or Streamlit secrets."
#             )
#             return

#         try:
#             from mistralai import Mistral

#             self._client = Mistral(api_key=self.api_key)
#             self._available = True

#         except Exception as exc:  # pragma: no cover
#             self._init_error = str(exc)
#             self._available = False

#     @property
#     def is_available(self) -> bool:
#         return self._available

#     @property
#     def status_message(self) -> str:
#         if self._available:
#             return "Chatbot ready."
#         return self._init_error or "Chatbot unavailable."

#     def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
#         if not self._available or self._client is None:
#             return (
#                 "Chatbot is offline. Set MISTRAL_API_KEY in .env (local) or "
#                 "[secrets] in Streamlit Cloud, then restart the app.\n\n"
#                 f"Details: {self._init_error}"
#             )

#         try:
#             messages = self._format_history(history or [])
#             messages.append({"role": "user", "content": message})

#             response = self._client.chat.complete(
#                 model=self.model_name,
#                 messages=messages
#             )

#             return (response.choices[0].message.content or "").strip() or "No response from the model."

#         except Exception as exc:
#             return f"Sorry, the chat request failed: {exc}"

#     @staticmethod
#     def _format_history(history: List[dict]) -> List[dict]:
#         """Convert Streamlit-style messages to Mistral chat history."""
#         formatted = []
#         for item in history:
#             role = item.get("role", "user")
#             content = item.get("content", "")
#             if not content:
#                 continue

#             # Mistral uses: system | user | assistant
#             if role == "assistant":
#                 formatted.append({"role": "assistant", "content": content})
#             else:
#                 formatted.append({"role": "user", "content": content})

#         return formatted

# """Gemini-powered fitness chatbot."""

# from __future__ import annotations

# import os
# from typing import List, Optional

# from dotenv import load_dotenv

# load_dotenv()

# SYSTEM_PROMPT = """You are a certified-style fitness coach assistant embedded in an AI workout app.
# Give practical, safe, evidence-informed answers about exercise form, programming, recovery, and nutrition basics.
# - Prefer concise bullet points when listing steps.
# - Always remind users to consult a doctor for pain, injury, or medical conditions.
# - Do not diagnose diseases or prescribe medication.
# - When rep counting or pose tech is mentioned, explain that the app uses joint-angle tracking (works from many camera angles).
# """


# class FitnessChatbot:
#     def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash") -> None:
#         self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "").strip()
#         self.model_name = model_name
#         self._model = None
#         self._available = False
#         self._init_error: Optional[str] = None
#         self._configure()

#     def _configure(self) -> None:
#         if not self.api_key:
#             self._init_error = (
#                 "GOOGLE_API_KEY is missing. Add it to a .env file or Streamlit secrets."
#             )
#             return
#         try:
#             import google.generativeai as genai

#             genai.configure(api_key=self.api_key)
#             self._model = genai.GenerativeModel(
#                 model_name=self.model_name,
#                 system_instruction=SYSTEM_PROMPT,
#             )
#             self._available = True
#         except Exception as exc:  # pragma: no cover
#             self._init_error = str(exc)
#             self._available = False

#     @property
#     def is_available(self) -> bool:
#         return self._available

#     @property
#     def status_message(self) -> str:
#         if self._available:
#             return "Chatbot ready."
#         return self._init_error or "Chatbot unavailable."

#     def chat(self, message: str, history: Optional[List[dict]] = None) -> str:
#         if not self._available or self._model is None:
#             return (
#                 "Chatbot is offline. Set GOOGLE_API_KEY in .env (local) or "
#                 "[secrets] in Streamlit Cloud, then restart the app.\n\n"
#                 f"Details: {self._init_error}"
#             )
#         try:
#             chat = self._model.start_chat(history=self._format_history(history or []))
#             response = chat.send_message(message)
#             return (response.text or "").strip() or "No response from the model."
#         except Exception as exc:
#             return f"Sorry, the chat request failed: {exc}"

#     @staticmethod
#     def _format_history(history: List[dict]) -> List[dict]:
#         """Convert Streamlit-style messages to Gemini chat history."""
#         formatted = []
#         for item in history:
#             role = item.get("role", "user")
#             content = item.get("content", "")
#             if not content:
#                 continue
#             if role == "assistant":
#                 formatted.append({"role": "model", "parts": [content]})
#             else:
#                 formatted.append({"role": "user", "parts": [content]})
#         return formatted
