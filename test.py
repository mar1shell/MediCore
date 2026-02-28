from mistralai import Mistral
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

with Mistral(
    api_key=os.getenv("MISTRAL_API_KEY", ""),
) as mistral:

    res = mistral.chat.complete(model="mistral-small-latest", messages=[
        {
            "content": "Who is the best French painter? Answer in one short sentence.",
            "role": "user",
        },
    ], stream=False)

    # Handle response
    print(res)

