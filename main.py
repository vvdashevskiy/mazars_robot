from bs4 import BeautifulSoup
from argparse import ArgumentParser
from datetime import datetime
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from dotenv import load_dotenv
import requests
import os
import json
import csv
import smtplib
import shutil

load_dotenv()

# TODO argparse
# TODO mail
# TODO mkdir tmp folder

_base_dir = os.path.abspath(os.getcwd()) + os.sep
_search_url = "https://api.semanticscholar.org/graph/v1/paper/search?query=" # api_url
_page_len = 10
_base_search_fields = ["title", "authors", "url", "abstract", "citationCount", "fieldsOfStudy", "isOpenAccess"]
_csv_header = ["title", "authors", "abstract", "citations", "source", "pdf"]

parser = ArgumentParser(description="Argument Parser")
parser.add_argument("--topic", required=True, action="store", help="Topic name in quotes")
parser.add_argument("--pages", required=True, type=int, action="store", help="Number of pages of papers")
parser.add_argument("--pdf", required=False, action="store_true", help="Enable pdf downloading")
parser.add_argument("--email", required=False, action="store", help="Enable email notification to stated address")


def search_by_topic(topic: str, pages: int, **kwargs) -> list:
    request = _search_url + topic.replace(" ", "+")

    kwargs["limit"] = pages * _page_len

    if bool(kwargs):
        if "fields" in kwargs.keys() and type(kwargs["fields"]) is list:
            kwargs["fields"] = ",".join(kwargs["fields"])

        request += "&" + "&".join([f"{k}={v}" for k, v in kwargs.items() if v is not None])

    response = requests.get(request).text

    data = json.loads(response)

    return [{
        "title": x["title"],
        "source": x["url"],
        "description": x["abstract"],
        "citations": x["citationCount"],
        "authors": ", ".join([author["name"] for author in x["authors"]])
    } for x in data["data"] if x["isOpenAccess"]]


def get_topic_info(topic_list: list):
    """updates current topic list with source and pdf urls"""

    for topic in topic_list:
        text = requests.get(topic["source"]).text
        parser = BeautifulSoup(text, 'html.parser')

        links = parser.body.findAll("a", {"data-selenium-selector": "paper-link"})

        topic["pdf"] = ""
        topic["source"] = ""

        for link in links:
            if link["href"].endswith(".pdf"):
                topic["pdf"] = link["href"]
            else:
                topic["source"] = link["href"]


def download_pdf(file_path: str, topic: dict):
    if "pdf" not in topic.keys() or topic["pdf"] == "":
        print("Cannot download file without url!")
        return

    try:
        response = requests.get(topic["pdf"], stream=True)
        if response.status_code == 200:
            with open(file_path + topic["title"] + ".pdf", "wb") as writer:
                for chunk in response:
                    writer.write(chunk)
    except:
        print(f"Cannot download pdf for {topic['title']}")


def convert_to_csv(file_path: str, topic_list: list):

    with open(f"{file_path}data.csv", "w+", encoding="utf-8", newline="\n") as writer:
        lines = [[x["title"],
                  x["authors"],
                  x["description"],
                  x["citations"],
                  x["source"],
                  x["pdf"]] for x in topic_list]

        csv_writer = csv.writer(writer, delimiter=";")
        csv_writer.writerows([_csv_header] + lines)


def send_email(file_path: str, title: str, to: str):
    message = MIMEMultipart()

    message["From"] = os.getenv("LOGIN")
    message["To"] = to
    message["Subject"] = f"{title} compiled data"

    shutil.make_archive(title, "zip", file_path)

    with open(title + ".zip", "rb") as reader:
        attachment = MIMEBase("application", "octet-stream")
        attachment.set_payload(reader.read())
        encoders.encode_base64(attachment)
        attachment.add_header("Content-Disposition", f"attachment; filename={title}.zip")
        message.attach(attachment)

    with smtplib.SMTP("smtp.office365.com") as sender:
        sender.starttls()
        sender.login(os.getenv("LOGIN"), os.getenv("PASSWORD"))
        sender.sendmail(message["From"], message["To"], message.as_string())


if __name__ == "__main__":
    args = parser.parse_args()
    print(args)

    current_date = int(datetime.now().timestamp())

    folder_name = f"{args.topic.replace(' ', '_')}_{current_date}"
    path = _base_dir + folder_name + os.sep

    os.mkdir(path)

    topics = search_by_topic(args.topic, args.pages, fields=_base_search_fields)

    get_topic_info(topics)

    if args.pdf:
        for topic in topics:
            download_pdf(path, topic)

    convert_to_csv(path, topics)

    if args.email is not None:
        send_email(path, args.topic, args.email)
