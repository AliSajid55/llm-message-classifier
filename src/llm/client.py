import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)


def get_client():
    return OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )


def get_model():
    return os.environ.get("LLM_MODEL", "openrouter/free")
