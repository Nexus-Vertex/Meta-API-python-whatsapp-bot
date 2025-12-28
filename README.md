## Setup & Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/whatsapp-bot.git
cd whatsapp-bot
2️⃣ Install dependencies
bash
Copier le code
pip install -r requirements.txt
Environment Variables
Create a .env file in the root folder of the project:

env
Copier le code
APP_ID=your_app_id_here
APP_SECRET=your_app_secret_here
ACCESS_TOKEN=your_access_token_here
VERIFY_TOKEN=your_verify_token_here
RECIPIENT_WAID=your_test_number_here
VERSION=v18.0
OPENAI_API_KEY=your_openai_api_key
OPENAI_ASSISTANT_ID=your_assistant_id
Variables explanation
Variable	Description
APP_ID	WhatsApp Business App ID
APP_SECRET	App secret from Meta
ACCESS_TOKEN	WhatsApp API access token
VERIFY_TOKEN	Webhook verification token
RECIPIENT_WAID	Test WhatsApp number
VERSION	Meta Graph API version
OPENAI_API_KEY	OpenAI API key
OPENAI_ASSISTANT_ID	OpenAI Assistant ID

Running the App
Start the Flask server locally:

bash
Copier le code
python run.py
The server will run on:
👉 http://localhost:8000/

Ngrok & Webhook Integration
1️⃣ Install ngrok
👉 https://ngrok.com/download

2️⃣ Authenticate ngrok
bash
Copier le code
ngrok authtoken YOUR_AUTH_TOKEN
3️⃣ Expose your local server
bash
Copier le code
ngrok http 8000 --domain your-domain.ngrok-free.app
4️⃣ Configure Webhook in Meta Dashboard
Go to WhatsApp → Configuration

Callback URL:

arduino
Copier le code
https://your-domain.ngrok-free.app/webhook
Verify Token: same value as VERIFY_TOKEN

Subscribe to messages and statuses

Click Test

✅ Webhook is now connected.

Testing the Bot
Add your test number to WhatsApp contacts

Send a message to the bot

Check terminal logs:

text
Copier le code
Received message: {"from": "...", "text": "..."}
By default, the bot replies with uppercase text.

AI Integration
Update generate_response() in whatsapp_utils.py

Configure OpenAI logic in openai_service.py

Set OpenAI keys in .env

Call AI inside process_whatsapp_message()

📌 The bot can now reply intelligently using AI.

Add Your Phone Number
For production use:

Add a real phone number in Meta Dashboard

Migrate existing numbers if required

Safe testing options:
New SIM card

Virtual phone number

Secondary device

Security Notes
Verify webhook using hub.verify_token

Validate X-Hub-Signature-256 using APP_SECRET

Accept requests only from Meta servers

Tips for Production
Use a VPS or cloud server

Use long-lived access tokens

Secure .env file

Enable logging and monitoring

Keep dependencies updated

References
WhatsApp Cloud API
https://developers.facebook.com/docs/whatsapp

OpenAI API
https://platform.openai.com/docs

Ngrok Documentation
https://ngrok.com/docs

YouTube Tutorials
https://www.youtube.com/@daveebbelaar

💡 Note:
This README section is fully formatted and ready to be copied directly into GitHub README.md.
