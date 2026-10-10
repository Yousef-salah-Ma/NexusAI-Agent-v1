from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.tools import tool
from langchain_tavily import TavilySearch
from langchain_postgres import PGVector
from email.message import  EmailMessage
import smtplib
import re
import imaplib
import email
from email.header import decode_header
from email.utils import parseaddr
from html import unescape , escape
from html.parser import HTMLParser
import ast
import operator
import math
import os

import json
from datetime import datetime
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
)
from openpyxl import Workbook
from dotenv import load_dotenv


REPORTS_DIR = Path("./reports")

load_dotenv()
FROM_EMAIL = os.environ.get("FROM_EMAIL")

PASSWORD_EMAIL= os.environ.get("PASSWORD_EMAIL")

CONNECTION=os.environ.get("CONNECTION")
api_key = os.environ.get("tavily_api_key")

embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cuda"},
    encode_kwargs={"normalize_embeddings": True}
)

vector_store = PGVector(
    embeddings=embedding_model,
    collection_name="my_documents",
    connection=CONNECTION,
)


@tool
def local_search(query: str):
    """
    Search the local vector database for relevant information from the
    indexed documents.

    Use this tool when the user asks a question that may be answered
    using information stored in the local document collection.

    The tool performs a semantic similarity search and retrieves the
    5 most relevant document chunks related to the user's query.
    It returns the retrieved text as a single string that can be used
    as context to answer the user's question.

    Args:
        query: A natural-language search query describing the information
               you want to find in the local documents.

    Returns:
        The text content of the 5 most relevant document chunks.
    """
    
    ret = vector_store.similarity_search(query, k=5)

    return "\n".join(i.page_content for i in ret)

def format_search_results(data):
    return "\n\n".join(
        f"Title: {result['title']}\n"
        f"Content: {result['content']}"
        for result in data["results"]
    )


client = TavilySearch(api_key=api_key)


@tool
def web_search(query: str):
    """
    Search the web for relevant and up-to-date information.

    Use this tool when the user asks about information that may not be
    available in the local knowledge base, or when current, external,
    or real-time information is needed.

    The tool returns relevant search results containing titles and
    content that can be used as context to answer the user's question.

    Args:
        query: A natural-language search query describing the information
               to look for on the web.

    Returns:
        Formatted web search results containing relevant titles and content.
    """
    
    data = client.invoke(query)

    return format_search_results(data)

@tool
def send_mail(email: str, Subject: str, content_send: str) -> str:
    """
    Send an email using Gmail SMTP.

    Use this tool when the user asks to send an email.

    Args:
        email: The recipient's email address.
        Subject: The subject of the email.
        content_send: The body of the email.

    Returns:
        A string describing whether the email was sent successfully
        or whether an error occurred.
    """
    msg = EmailMessage()
    msg["Subject"] = Subject
    msg["From"] = FROM_EMAIL
    msg["To"] = email
    msg.set_content(content_send)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(FROM_EMAIL, PASSWORD_EMAIL)
            rejected = server.send_message(msg)

        if rejected:
            return f"Email rejected for recipients: {', '.join(rejected.keys())}"

        return f"Email sent successfully to {email}."

    except (smtplib.SMTPException, OSError) as e:
        return f"Email sending failed: {e}"



class HTMLTextParser(HTMLParser):
    """Extract readable text from HTML emails."""

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def get_text(self):
        return " ".join(self.parts)


def decode_value(value):
    """Decode email headers such as Subject and From."""

    if not value:
        return ""

    parts = decode_header(value)
    result = []

    for part, encoding in parts:
        if isinstance(part, bytes):
            result.append(
                part.decode(encoding or "utf-8", errors="replace")
            )
        else:
            result.append(part)

    return "".join(result)


def extract_body(msg):
    """Extract readable text while skipping attachments."""

    plain_parts = []
    html_parts = []

    parts = msg.walk() if msg.is_multipart() else [msg]

    for part in parts:
        if part.get_content_disposition() == "attachment":
            continue

        content_type = part.get_content_type()

        if content_type not in ("text/plain", "text/html"):
            continue

        payload = part.get_payload(decode=True)

        if payload is None:
            continue

        charset = part.get_content_charset() or "utf-8"

        text = payload.decode(charset, errors="replace")

        if content_type == "text/plain":
            plain_parts.append(text)

        elif content_type == "text/html":
            parser = HTMLTextParser()
            parser.feed(text)
            html_parts.append(unescape(parser.get_text()))

    # Prefer plain text when available.
    if plain_parts:
        return "\n".join(plain_parts).strip()

    return "\n".join(html_parts).strip()


def quote_imap(value):
    """Quote a search value and reject IMAP command injection."""

    if "\r" in value or "\n" in value:
        raise ValueError("Invalid search value.")

    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


@tool
def read_emails(
    search_type: str,
    sender: str = "",
    content_query: str = "",
    limit: int = 1
) -> str:
    """
    Search and read emails from Gmail Inbox.

    search_type:
        latest: Read the latest emails.
        sender: Find emails from a specific email address.
        content: Find emails containing specified text.

    sender: The sender's email address.
    content_query: Text to search for in email content.
    limit: Maximum number of emails to return, from 1 to 10.
    """

    if search_type not in {"latest", "sender", "content"}:
        return "Error: search_type must be latest, sender, or content."

    if not isinstance(limit, int) or isinstance(limit, bool):
        return "Error: limit must be an integer."

    if not 1 <= limit <= 10:
        return "Error: limit must be between 1 and 10."

    if search_type == "sender":
        if not sender or "\r" in sender or "\n" in sender:
            return "Error: provide a valid sender email address."

        _, address = parseaddr(sender)

        if not re.fullmatch(r"[^@\s<>]+@[^@\s<>]+\.[^@\s<>]+", address):
            return "Error: provide a valid sender email address."

    if search_type == "content":
        if not content_query or not content_query.strip():
            return "Error: provide content_query."

        if "\r" in content_query or "\n" in content_query:
            return "Error: invalid content query."

    if not FROM_EMAIL or not PASSWORD_EMAIL:
        return "Error: email credentials are missing from .env."

    mail = None

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(FROM_EMAIL, PASSWORD_EMAIL)

        status, _ = mail.select("INBOX", readonly=True)

        if status != "OK":
            return "Error: could not open Inbox."

        # Choose the search criteria.
        if search_type == "latest":
            criteria = ["ALL"]

        elif search_type == "sender":
            criteria = ["FROM", quote_imap(address)]

        else:
            criteria = ["TEXT", quote_imap(content_query.strip())]

        status, data = mail.search(None, *criteria)

        if status != "OK":
            return "Error: email search failed."

        email_ids = data[0].split()

        if not email_ids:
            return "No matching emails found."

        # IDs returned by IMAP are in mailbox sequence order.
        selected_ids = list(reversed(email_ids[-limit:]))

        results = []

        for email_id in selected_ids:
            status, data = mail.fetch(email_id, "(RFC822)")

            if status != "OK":
                continue

            raw_message = next(
                (
                    item[1]
                    for item in data
                    if isinstance(item, tuple)
                ),
                None
            )

            if raw_message is None:
                continue

            msg = email.message_from_bytes(raw_message)

            subject = decode_value(msg.get("Subject"))
            from_header = decode_value(msg.get("From"))
            date = msg.get("Date", "Unknown date")
            body = extract_body(msg)

            # Verify sender locally as an extra check.
            if search_type == "sender":
                actual_sender = parseaddr(from_header)[1].lower()

                if actual_sender != address.lower():
                    continue

            results.append(
                f"From: {from_header}\n"
                f"Subject: {subject}\n"
                f"Date: {date}\n"
                f"Body:\n{body[:6000]}"
            )

        if not results:
            return "No readable matching emails found."

        return "\n\n" + ("\n\n" + "=" * 40 + "\n\n").join(results)

    except (imaplib.IMAP4.error, OSError) as exc:
        return f"Email connection error: {exc}"

    except Exception as exc:
        return f"Error reading emails: {exc}"

    finally:
        if mail is not None:
            try:
                mail.logout()
            except Exception:
                pass


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def calculate_node(node):
    if isinstance(node, ast.Expression):
        return calculate_node(node.body)

    if isinstance(node, ast.Constant):
        if type(node.value) not in (int, float):
            raise ValueError("Only numbers are allowed")
        return node.value

    if isinstance(node, ast.BinOp):
        op_type = type(node.op)

        if op_type not in OPERATORS:
            raise ValueError("Unsupported operation")

        left = calculate_node(node.left)
        right = calculate_node(node.right)

        if op_type is ast.Pow:
            if abs(right) > 100 or abs(left) > 1_000_000:
                raise ValueError("Exponent is too large")

        result = OPERATORS[op_type](left, right)

        if isinstance(result, (int, float)):
            if not math.isfinite(result):
                raise ValueError("Result is too large or invalid")

        return result

    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)

        if op_type not in (ast.USub, ast.UAdd):
            raise ValueError("Unsupported operation")

        return OPERATORS[op_type](calculate_node(node.operand))

    raise ValueError("Invalid mathematical expression")


@tool
def calculator(expression: str) -> str:
    """
    Calculate a mathematical expression accurately.

    Use this tool for arithmetic calculations involving addition,
    subtraction, multiplication, division, parentheses, and powers.

    Args:
        expression: A mathematical expression, such as "25 * 4 + 10".

    Returns:
        The calculation result or an error message.
    """
    try:
        tree = ast.parse(expression, mode="eval")
        result = calculate_node(tree)

        return str(result)

    except (ValueError, TypeError, ZeroDivisionError, OverflowError, SyntaxError) as e:
        return f"Calculation error: {e}"



@tool
def create_report(content: str, file_type: str) -> str:
    """
    Create a report file for the user.

    Args:
        content: The complete report content.
        file_type: Choose pdf for formatted reports,
                   excel for tables and structured data,
                   or text for simple notes.

    Returns JSON containing the file name and type on success.
    """

    try:
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

        file_type = file_type.strip().lower()

        if file_type not in {"pdf", "excel", "text"}:
            return json.dumps({
                "status": "error",
                "message": "file_type must be pdf, excel, or text."
            })

        # Unique filename to avoid collisions
        filename_id = __import__("uuid").uuid4().hex

        # 1. TEXT
        if file_type == "text":
            file_path = REPORTS_DIR / f"report_{filename_id}.txt"
            file_path.write_text(content, encoding="utf-8")

        # 2. PDF
        elif file_type == "pdf":
            file_path = REPORTS_DIR / f"report_{filename_id}.pdf"

            document = SimpleDocTemplate(
                str(file_path),
                pagesize=A4,
                title="Generated Report",
            )

            styles = getSampleStyleSheet()
            story = []

            for line in content.splitlines():
                if line.strip():
                    story.append(
                        Paragraph(
                            escape(line),
                            styles["BodyText"]
                        )
                    )
                else:
                    story.append(Spacer(1, 8))

            document.build(story)

        # 3. EXCEL
        else:
            file_path = REPORTS_DIR / f"report_{filename_id}.xlsx"

            workbook = Workbook()
            sheet = workbook.active
            sheet.title = "Report"

            try:
                data = json.loads(content)
            except json.JSONDecodeError:
                data = None

            if isinstance(data, list) and data:
                if all(isinstance(row, dict) for row in data):
                    headers = list(
                        dict.fromkeys(
                            key
                            for row in data
                            for key in row.keys()
                        )
                    )

                    sheet.append(headers)

                    for row in data:
                        sheet.append([
                            row.get(key, "")
                            for key in headers
                        ])

                elif all(isinstance(row, list) for row in data):
                    for row in data:
                        sheet.append(row)

                else:
                    sheet.append(["Content"])
                    sheet.append([content])

            else:
                sheet.append(["Content"])

                for line in content.splitlines():
                    sheet.append([line])

            for column in sheet.columns:
                column_letter = column[0].column_letter

                max_length = max(
                    len(str(cell.value or ""))
                    for cell in column
                )

                sheet.column_dimensions[column_letter].width = min(
                    max_length + 2, 45
                )

            workbook.save(file_path)

        return json.dumps({
            "status": "success",
            "file_name": file_path.name,
            "file_type": file_type
        })

    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"{type(e).__name__}: {e}"
        })
