import json
import os
import re
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler

from supabase import create_client

def send(handler, status, payload):
    body = json.dumps(payload).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", os.environ.get("ALLOWED_ORIGIN", "*"))
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        send(self, 200, {"ok": True})

    def do_POST(self):
        if self.path.rstrip("/") != "/api/bookings":
            return send(self, 404, {"error": "Endpoint not found."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 2 or length > 20000:
                return send(self, 400, {"error": "Invalid request size."})
            data = json.loads(self.rfile.read(length))
            name = str(data.get("name", "")).strip()
            email = str(data.get("email", "")).strip().lower()
            role = str(data.get("role", "Customer")).strip()
            booking_date = str(data.get("date", "")).strip()
            booking_time = str(data.get("time", "")).strip()
            service = str(data.get("service", "")).strip()
            message = str(data.get("message", "")).strip()

            if not name or len(name) > 100:
                return send(self, 400, {"error": "Enter a name of up to 100 characters."})
            if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or len(email) > 254:
                return send(self, 400, {"error": "Enter a valid email address."})
            if role not in ("Customer", "Provider"):
                return send(self, 400, {"error": "Invalid role."})
            try:
                chosen_date = date.fromisoformat(booking_date)
                datetime.strptime(booking_time, "%H:%M")
            except ValueError:
                return send(self, 400, {"error": "Choose a valid date and time."})
            if chosen_date < date.today():
                return send(self, 400, {"error": "The appointment date cannot be in the past."})
            if service not in ("Introductory call", "Project consultation", "Portfolio review"):
                return send(self, 400, {"error": "Choose a valid appointment type."})
            if len(message) > 1000:
                return send(self, 400, {"error": "Message must be 1,000 characters or fewer."})

            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            if not url or not key:
                return send(self, 503, {"error": "Backend is not configured. Add the Supabase environment variables in Vercel."})
            client = create_client(url, key)
            result = client.table("appointments").insert({
                "name": name, "email": email, "role": role,
                "appointment_date": booking_date, "appointment_time": booking_time,
                "service": service, "message": message, "status": "pending"
            }).execute()
            row = result.data[0]
            return send(self, 201, {"id": row["id"], "status": row["status"]})
        except json.JSONDecodeError:
            return send(self, 400, {"error": "Request must contain valid JSON."})
        except Exception:
            # Avoid leaking service keys, SQL details, or internal stack traces to visitors.
            return send(self, 500, {"error": "Could not save booking. Check the server logs and Supabase setup."})
