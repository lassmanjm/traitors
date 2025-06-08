from openai import OpenAI
import os
from absl import flags
import constants


FLAGS = flags.FLAGS
flags.DEFINE_string(
    "openai_model",
    "",
    "The model type to use in the OpenAI api calls.",
)
flags.DEFINE_string(
    "openai_api_key",
    "",
    "The model type to use in the OpenAI api calls.",
)


class Conversation:
    def __init__(self):
        model_flag = FLAGS.openai_model
        model_environ = os.environ.get("OPENAI_MODEL")
        self.model = (
            model_flag if model_flag else model_environ if model_environ else "gpt-4.1"
        )

        self.client = OpenAI()
        self.reset_context()

    def reset_context(self):
        self.messages = []

        self.messages.append(
            {
                "role": "system",
                "content": constants.kClaudiaSystemPrompt,
            }
        )

    def send_message(self, user_message: str):
        # Add user message to conversation history
        self.messages.append({"role": "user", "content": user_message})

        # Get response from API
        completion = self.client.chat.completions.create(
            model=self.model, messages=self.messages
        )

        # Extract assistant's response
        assistant_response = completion.choices[0].message.content

        # Add assistant's response to conversation history
        self.messages.append({"role": "assistant", "content": assistant_response})

        return assistant_response

    def get_conversation_history(self):
        return self.messages.copy()

    def clear_conversation(self):
        # Keep system message if it exists
        system_messages = [msg for msg in self.messages if msg["role"] == "system"]
        self.messages = system_messages
