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

whatsapp-bot/
├── webhook.py # Main file to start Flask server
├── requirements.txt # Python dependencies
├── utils.py # Functions to handle WhatsApp messages
├── update_excel_realtime.py # Functions to update Excel in real-time
├── database.db # (Optional) SQLite database
├── .env # Environment variables
└── README.md # Documentation

yaml
Copier le code

---

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
Create a .env file in the root folder:

env
Copier le code
ACCESS_TOKEN="your_access_token_here"
APP_SECRET="your_app_secret_here"
VERIFY_TOKEN="your_verify_token_here"
APP_ID="your_app_id_here"
Variables explanation:

Variable	Description
ACCESS_TOKEN	WhatsApp API access token
APP_SECRET	App secret from Meta
VERIFY_TOKEN	Webhook verification token
APP_ID	WhatsApp Business App ID

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

text
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

References
WhatsApp Cloud API
👉 https://developers.facebook.com/docs/whatsapp

OpenAI API
👉 https://platform.openai.com/docs

Ngrok
👉 https://ngrok.com/docs

YouTube Tutorials
👉 https://www.youtube.com/@daveebbelaar
