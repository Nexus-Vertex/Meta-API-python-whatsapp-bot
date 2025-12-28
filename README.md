WhatsApp AI Bot with Python & Flask

This project demonstrates how to create a WhatsApp bot using the Meta (formerly Facebook) Cloud API with pure Python and Flask. The bot integrates webhook events to receive messages in real-time and can generate AI responses using OpenAI.

Table of Contents

Prerequisites

Setup & Installation

Environment Variables

Running the App

Ngrok & Webhook Integration

Testing the Bot

AI Integration

Add Your Phone Number

Security Notes

References

Prerequisites

A Meta Developer Account — If you don’t have one, you can create a Meta Developer Account here

A WhatsApp Business App — Learn how to create a business app here

Familiarity with Python & Flask to follow the tutorial

Setup & Installation

Clone this repository:

git clone https://github.com/YOUR_USERNAME/whatsapp-bot.git
cd whatsapp-bot


Install dependencies:

pip install -r requirements.txt


Create .env file based on example.env and fill in your credentials

Environment Variables

APP_ID - Your WhatsApp Business App ID

APP_SECRET - Your WhatsApp Business App Secret

ACCESS_TOKEN - Meta Graph API Access Token

VERIFY_TOKEN - Token for webhook verification

RECIPIENT_WAID - WhatsApp number to send test messages

VERSION - API version (v18.0)

Running the App
python run.py

Ngrok & Webhook Integration

Sign up for ngrok (https://ngrok.com/
)

Download & authenticate your agent

Start ngrok to expose localhost:

ngrok http 8000 --domain your-domain.ngrok-free.app


Copy the URL and paste in Meta App Dashboard → WhatsApp → Webhook Callback URL (https://your-domain.ngrok-free.app/webhook)

Enter your VERIFY_TOKEN

Subscribe to message events and test the connection

Testing the Bot

Add the test number to your WhatsApp contacts

Send a message and check if the bot replies

Monitor logs in terminal

AI Integration

Update whatsapp_utils.py with your generate_response() function

Connect OpenAI Assistant API with your OPENAI_API_KEY

Provide data & instructions in openai_service.py

Test AI responses by sending messages to your bot

Add Your Phone Number

Add your personal/production WhatsApp number in Meta App

You may need to migrate existing numbers to Business API

Options for testing without affecting your personal number:

Virtual number

New SIM card

Dual SIM or dedicated device

Security Notes

Webhook verification using hub.verify_token

Payload signed with SHA256 in X-Hub-Signature-256 header

Compare signature with your APP_SECRET

References

WhatsApp API Documentation

OpenAI API Documentation

Ngrok Documentation

YouTube tutorials: Dave Ebbelaar
