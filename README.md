# WhatsApp AI Bot with Python & Flask 🤖📱

This project demonstrates how to build a WhatsApp bot using the **Meta (Facebook) Cloud API**, **Python**, and **Flask**.  
The bot supports real-time messaging via webhooks and can generate **AI-powered responses using OpenAI**.

This guide walks you **step-by-step**, from initial setup to AI integration, just like an official tutorial.

---

## 📑 Table of Contents

- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Environment Variables](#environment-variables)
- [Running the App](#running-the-app)
- [Ngrok & Webhook Integration](#ngrok--webhook-integration)
- [Testing the Bot](#testing-the-bot)
- [AI Integration](#ai-integration)
- [Add Your Phone Number](#add-your-phone-number)
- [Security Notes](#security-notes)
- [Tips for Production](#tips-for-production)
- [References](#references)

---

## Prerequisites

Before starting, make sure you have:

- **Meta Developer Account**  
  👉 https://developers.facebook.com/

- **WhatsApp Business App**  
  👉 https://developers.facebook.com/apps/

- **Python 3.10+** installed on your system  
  👉 https://www.python.org/downloads/

- Basic knowledge of **Python**, **Flask**, and **HTTP APIs**

---

## Project Structure

Recommended project structure:

```text
whatsapp-bot/
├── webhook.py             # Main file to start Flask server
├── requirements.txt       # Python dependencies
├── utils.py               # Functions to handle WhatsApp messages
├── update_excel_realtime.py      # Functions to handle WhatsApp messages
├── database.db            # (Optional) SQLite database
├── .env                   # Environment variables
└── README.md              # Documentation

Setup & Installation
1️⃣ Clone the repository
bash
Copier le code
git clone https://github.com/YOUR_USERNAME/whatsapp-bot.git
cd whatsapp-bot

2️⃣ Install dependencies
bash
Copier le code
pip install -r requirements.txt
Environment Variables
Create a .env file in the root folder:

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
ACCESS_TOKEN	WhatsApp API token
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
Server will run on:
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
Verify Token: same as VERIFY_TOKEN

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

Configure OpenAI in openai_service.py

Set OpenAI keys in .env

Call AI inside process_whatsapp_message()

📌 The bot can now reply intelligently using AI.

Add Your Phone Number
For production use:

Add a real phone number in Meta Dashboard

Migrate existing numbers if needed

Safe testing options:
New SIM card

Virtual phone number

Secondary device

Security Notes
Verify webhook using hub.verify_token

Validate X-Hub-Signature-256 with APP_SECRET

Accept requests only from Meta servers

Tips for Production
Use a VPS or cloud server

Use long-lived access tokens

Secure .env file

Enable logging & monitoring

Keep dependencies updated

References
WhatsApp Cloud API
https://developers.facebook.com/docs/whatsapp

OpenAI API
https://platform.openai.com/docs

Ngrok
https://ngrok.com/docs

YouTube Tutorials
https://www.youtube.com/@daveebbelaar
