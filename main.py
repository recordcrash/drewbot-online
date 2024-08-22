from fasthtml.common import (
    FastHTML, Div, Form, Input, Button, Body, Title, H1, H4, Span, Img, Style, FileResponse, serve
)
from openai import OpenAI
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom CSS for Discord-like styling
discord_style = Style('''
    :root {
        --background-tertiary: #202225;
        --background-secondary: #2f3136;
        --background-primary: #36393f;
        --text-normal: #dcddde;
        --text-muted: #72767d;
        --header-primary: #fff;
        --interactive-normal: #b9bbbe;
        --brand-experiment: #5865f2;
    }
    body {
        font-family: Whitney, 'Helvetica Neue', Helvetica, Arial, sans-serif;
        background-color: var(--background-tertiary);
        color: var(--text-normal);
        margin: 0;
        padding: 0;
        height: 100vh;
        display: flex;
        flex-direction: column;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        height: 100%;
        background-color: var(--background-primary);
    }
    .chat-header {
        background-color: var(--background-secondary);
        padding: 16px;
        box-shadow: 0 1px 0 rgba(4,4,5,0.2),0 1.5px 0 rgba(6,6,7,0.05),0 2px 0 rgba(4,4,5,0.05);
    }
    .chat-header h1 {
        color: var(--header-primary);
        font-size: 16px;
        font-weight: 600;
        margin: 0;
    }
    .chat-header h4 {
        color: var(--text-muted);
        font-size: 12px;
        font-weight: 400;
        margin: 4px 0 0;
    }
    #chatlist {
        flex-grow: 1;
        overflow-y: auto;
        padding: 16px;
    }
    .message {
        display: flex;
        margin-bottom: 16px;
        padding: 2px 0;
    }
    .message-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin-right: 16px;
    }
    .message-content {
        flex-grow: 1;
    }
    .message-header {
        display: flex;
        align-items: baseline;
        margin-bottom: 4px;
    }
    .message-username {
        font-size: 1em;
        font-weight: 500;
        color: var(--header-primary);
        margin-right: 8px;
    }
    .message-timestamp {
        font-size: 0.75em;
        color: var(--text-muted);
    }
    .message-body {
        font-size: 1em;
        line-height: 1.375rem;
        color: var(--text-normal);
        white-space: pre-wrap;
    }
    .chat-input {
        background-color: var(--background-secondary);
        padding: 16px;
    }
    .chat-input form {
        display: flex;
    }
    .chat-input input {
        flex-grow: 1;
        background-color: var(--background-tertiary);
        border: none;
        border-radius: 8px;
        color: var(--text-normal);
        padding: 10px 16px;
        font-size: 1em;
    }
    .chat-input button {
        background-color: var(--brand-experiment);
        color: #fff;
        border: none;
        border-radius: 3px;
        padding: 10px 16px;
        margin-left: 16px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
    }
    .clear-history-btn {
        background-color: var(--brand-experiment);
        color: #fff;
        border: none;
        border-radius: 3px;
        padding: 8px 12px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        position: absolute;
        top: 16px;
        right: 16px;
    }
    
    .chat-header {
        position: relative;
    }
''')

# Set up the app with custom Discord-like styling
app = FastHTML(hdrs=(discord_style,), ws_hdr=True)

# Set up a chat model client and list of messages
cli = OpenAI()
model = "ft:gpt-4o-2024-08-06:record-crash:drew4o-qheart:9ySQQ0kC"
model_string = model.split(":")[-2]
sp = ("You are Drew Linky, a Discord chatbot that receives messages by users and returns original "
      "responses. You are a sarcastic biologist with a passion for video games, particularly "
      "Zelda, bread and some other eclectic media like Homestuck. You will receive a list of "
      "messages preceded by their usernames, and append your response body at the end. "
      "In addition, you will make sure to write long, coherent replies.")
messages = []


# Converts invisible message contents to visible ones
def visible_message_content(msg_content):
    return msg_content if not msg_content.startswith("hsd_user: ") else msg_content[
                                                                        len("hsd_user: "):-len("\ndrewlinky:")]


# Chat message component (renders a Discord-like message)
def chat_message(msg_idx):
    msg = messages[msg_idx]
    avatar_src = "user-avatar.gif" if msg['role'] == 'user' else "avatar.jpg"
    return Div(
        Img(src=avatar_src, cls="message-avatar"),
        Div(
            Div(
                Span("User" if  msg['role'] == 'user' else "Drew Linky", cls="message-username"),
                Span("Today", cls="message-timestamp"),
                cls="message-header"
            ),
            Div(visible_message_content(msg['content']),
                id=f"chat-content-{msg_idx}",
                cls="message-body"),
            cls="message-content"
        ),
        id=f"chat-message-{msg_idx}",
        cls="message"
    )


# The input field for the user message
def chat_input():
    return Input(type="text", name='msg', id='msg-input',
                 placeholder="Message @Drew Linky",
                 cls="chat-input-field")


# The main screen
@app.route("/")
def home():
    title = "Drewbot Online"
    page = Body(
        Div(
            Div(
                H1(title),
                H4(f"Currently using {model_string}"),
                Button("Clear History", id="clear-history-btn", cls="clear-history-btn", hx_post="/clear-history",
                       hx_target="#chatlist", hx_swap="outerHTML"),
                cls="chat-header"
            ),
            Div(*[chat_message(msg_idx) for msg_idx, msg in enumerate(messages)],
                id="chatlist"),
            Div(
                Form(
                    chat_input(),
                    Button("Send", cls="chat-send-button"),
                    ws_send=True, hx_ext="ws", ws_connect="/wscon",
                    cls="chat-input-form"
                ),
                cls="chat-input"
            ),
                cls="chat-container"
            )
    )
    return Title(title), page

@app.route("/{fname:path}.{ext:static}")
async def static(fname:str, ext:str):
    return FileResponse(f'{fname}.{ext}')


@app.ws('/wscon')
async def ws(msg: str, send):
    logger.info(f"WebSocket connection established. Messages: {len(messages)}")
    user_message_content = f"hsd_user: {msg}\ndrewlinky:"
    messages.append({"role": "user", "content": user_message_content})

    # Send the user message to the user (updates the UI right away)
    await send(Div(chat_message(len(messages) - 1), hx_swap_oob='beforeend', id="chatlist"))

    # Send the clear input field command to the user
    await send(chat_input())

    # Model response (streaming)
    # Prepare the full conversation history
    conversation_history = [{"role": "system", "content": sp}]
    for message in messages:
        role = message["role"]
        content = message["content"]
        if role == "user" and not content.startswith("hsd_user: "):
            content = f"hsd_user: {content}\ndrewlinky:"
        conversation_history.append({"role": role, "content": content})

    logger.info(conversation_history)

    r = cli.chat.completions.create(
        model=model,
        messages=conversation_history,
        stream=True,
        temperature=1.0,
    )

    # Send an empty message with the assistant response
    messages.append({"role": "assistant", "content": ""})
    await send(Div(chat_message(len(messages) - 1), hx_swap_oob='beforeend', id="chatlist"))

    # Fill in the message content
    for chunk in r:
        chunk_content = chunk.choices[0].delta.content or ""
        messages[-1]["content"] += chunk_content
        await send(Span(chunk_content, id=f"chat-content-{len(messages) - 1}", hx_swap_oob="beforeend"))

    logger.info(f"Message processed. Updated messages: {len(messages)}")


@app.route("/clear-history", methods=["POST"])
async def clear_history():
    global messages
    logger.info(f"Clearing history. Current messages: {len(messages)}")
    messages.clear()
    logger.info("History cleared")
    return Div(id="chatlist")

serve()