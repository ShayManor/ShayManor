import base64
import datetime
import json
import os
import time
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

import requests
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from supabase import create_client, Client

from email.message import EmailMessage

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

app = Flask(__name__, static_folder="src", static_url_path="")
CORS(app)


def get_body_system(date):
    return f"You are an expert at providing a real, accurate summary of the major news from the last day. You have access to web searches and hackernews. Summarize the top hackernews articles and **IMPORTANT** provide a realistic analysis and synthesis of these. Use understandable language and explain things well with relatively simple language. Don't use technical language if its not necessary. The current date is: {date}. Only return the overall summary as an article form and use critical thinking to analyze each. You will be given the top posts from hackernews and access to a web search tool and will use this to check the **MOST** interesting, relevant posts to talk about. Some interesting post example titles could be 'Using Claude Code to modernize a 25-year-old kernel driver', 'Myanmar – Silk Road of Surveillance', 'Stripe Launches L1 Blockchain: Tempo', 'LLM Visualization', or other interesting articles involving ML, math, cybersecurity, or crypto. Ignoring posts is fine. Focus on posts that talk about new technologies, AI/ML breakthroughts, or important relevant topics. Be concise, this should be a 2-5 minute read. Don't put a title, just the body in markdown. Only return the body, nothing else. Read the real articles, don't just use the titles. Go through the important links and summarize them."


def get_title_system():
    return "You are an expert at taking an article and giving it a short, clear title. No need for super dramatic titles. It should be 2-10 words and accurately encapsulate what happens and the overall theme. Only return the title."


def get_tldr_system():
    return "You are an expert at summarizing technical articles in a clear and understandable way. Without losing important information, write a 1 paragraph, short and clear tldr for this article. Be accurate. Only return the paragraph tldr summary. Don't start with TLDR or anything similar, just return the paragraph text."


@dataclass
class Article:
    by: str
    descendants: int
    id: int
    score: int
    time: int
    title: str
    type: str
    url: Optional[str]
    text: Optional[str]


def get_articles() -> str:
    articles = []
    ids_list = (
        requests.get("https://hacker-news.firebaseio.com/v0/topstories.json")
        .text[1:-1]
        .split(",")[:20]
    )
    for id in ids_list:
        raw_data = requests.get(
            f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
        ).text
        data = json.loads(raw_data)
        if data["type"] != "story":
            continue
        art = Article(
            data["by"],
            int(data["descendants"]),
            int(data["id"]),
            int(data["score"]),
            int(data["time"]),
            data["title"],
            data["type"],
            data.get("url", ""),
            data.get("text", ""),
        )
        articles.append(art)
    sorted_art = sorted(articles, key=lambda a: a.score, reverse=True)
    res = "{\n"
    for r in sorted_art:
        res += f"{r.title}:{r.url},\n"
    return res + "}"


@app.route("/", methods=["GET"])
def root():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<page>", methods=["GET"])
def any_page(page):
    return send_from_directory(app.static_folder, f"{page}")


@app.route("/create_blog_post", methods=["POST"])
def create_blog():
    try:
        data = request.get_json()
        SUPABASE_SERVICE_KEY = data["SUPABASE_SERVICE_KEY"]
        SUPABASE_URL = data["SUPABASE_URL"]
        OPENAI_API_KEY = data["OPENAI_API_KEY"]
        # Located here to block anyone from pinging this with spoofed keys
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

        def ping_gpt(system, prompt, effort, model="gpt-5") -> str:
            client = OpenAI(api_key=OPENAI_API_KEY)
            response = client.responses.create(
                model=model,
                reasoning={"effort": effort},
                input=prompt,
                instructions=system,
                tools=[{"type": "web_search"}],
            )
            return response.output_text

        articles = get_articles()
        current_date = date.today()
        body = ping_gpt(
            system=get_body_system(current_date.strftime("%B %d")),
            prompt=str(articles),
            effort="medium",
        )
        time.sleep(2)  # To stop rate limiting
        title = ping_gpt(
            system=get_title_system(), prompt=body, effort="low", model="gpt-5-mini"
        )
        time.sleep(2)
        tldr = ping_gpt(
            system=get_tldr_system(), prompt=body, effort="medium", model="gpt-5-nano"
        )

        id = str(uuid.uuid4())
        data_to_insert = {
            "id": id,
            "title": title,
            "body": body,
            "tldr": tldr,
            "articles": articles,
        }
        response = supabase.table("site_blog").insert(data_to_insert).execute()
        return jsonify({"status": id})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/add_email", methods=["POST"])
def add_email():
    try:
        data = request.get_json()
        email = data.get("email")
        frequency = data.get("frequency", "daily")
        if not email:
            raise ValueError("Email not found!")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")

        if not SUPABASE_SERVICE_KEY:
            return jsonify({"error": "No SUPABASE_SERVICE_KEY"})

        if not SUPABASE_URL:
            return jsonify({"error": "No SUPABASE_URL"})

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        data_to_insert = {"email": email, "frequency": frequency}
        response = supabase.table("site_users").insert(data_to_insert).execute()
        return jsonify({"status": 200})
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/remove_email", methods=["POST"])
def remove_email():
    try:
        data = request.get_json()
        email = data.get("email")
        if not email:
            raise ValueError("Email not found!")
        SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
        SUPABASE_URL = os.getenv("SUPABASE_URL")

        if not SUPABASE_SERVICE_KEY:
            return jsonify({"error": "No SUPABASE_SERVICE_KEY"})

        if not SUPABASE_URL:
            return jsonify({"error": "No SUPABASE_URL"})

        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        data_to_remove = {"email": email}
        response = supabase.table("site_users").delete(data_to_remove).execute()
        return jsonify({"status": 200})
    except Exception as e:
        return jsonify({"error": str(e)})


def execute(recipient: str, subject: str, content: str):
    """
    Sends email to given recipient. If an email is to a judge, put the word judge in the subject. Only sends to ONE recipient.
    :param recipient: email address to send to
    :return: "Email sent"
    """

    SCOPES = ["https://mail.google.com/"]
    creds = None
    if os.path.exists("/secrets/token/mail_token.json"):
        creds = Credentials.from_authorized_user_file(
            "/secrets/token/mail_token.json", SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "/secrets/client/gcloud_cfg.json", SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("/secrets/token/mail_token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()
        message.set_content(content)

        message["To"] = (
            recipient
        )
        message["From"] = "shay.manor@gmail.com"
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        send_message = (
            service.users().messages().send(userId="me", body=create_message).execute()
        )
        print(f"Message Id: {send_message['id']}")
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None
    return send_message


@app.route("/send_email", methods=["GET"])
def send_email():
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_URL = os.getenv("SUPABASE_URL")

    if not SUPABASE_SERVICE_KEY:
        return jsonify({"error": "No SUPABASE_SERVICE_KEY"}, 500)

    if not SUPABASE_URL:
        return jsonify({"error": "No SUPABASE_URL"}, 500)

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    current_day = datetime.datetime.now().weekday()
    if current_day == 6:
        response = supabase.table("site_users").select("email").execute()
    else:
        response = supabase.table("site_users").select("email").eq('frequency', 'daily').execute()
    emails = ",".join(x['email'] for x in response.data)
    print(emails)
    try:
        execute(recipient=emails, subject="test email", content="Shalom")
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
