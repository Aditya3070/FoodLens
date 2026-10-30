from flask import Flask, render_template, request, redirect, flash, session, url_for
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from db_config import get_db_connection
from utils.ocr import extract_text
from utils.groq_ai import analyze_ingredients
import bcrypt
import os
import json
import uuid

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# ---------------- CONFIG ---------------- #

UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


BODY_SYSTEM_ICONS = {
    "heart": "❤️ Heart",
    "blood_sugar": "🩸 Blood sugar",
    "brain": "🧠 Brain",
    "gut": "🫁 Gut",
    "kidneys": "🫘 Kidneys",
    "bones": "🦴 Bones",
    "immune_system": "🛡️ Immune system",
    "skin": "✨ Skin",
    "liver": "🫙 Liver",
    "blood_pressure": "📈 Blood pressure",
    "eyes": "👁️ Eyes",
    "blood_vessels": "🩹 Blood vessels",
}


@app.context_processor
def inject_globals():
    return dict(body_system_icons=BODY_SYSTEM_ICONS)


def group_by_body_system(analysis):
    """Group ingredients by the body systems they affect.
    Done in Python (not Jinja) because Jinja's {% set %} inside nested
    for-loops doesn't reliably persist dict mutations across scopes.
    """
    systems = {}
    for ing in analysis.get("ingredients", []):
        for sys in ing.get("body_systems_affected", []):
            systems.setdefault(sys, []).append(ing)
    return systems


def login_required(view):
    """Small helper to avoid repeating the same session check everywhere."""
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login first.")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ---------------- #

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fullname = request.form.get("fullname", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not fullname or not email or not password:
            flash("Please fill in all fields.")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for("register"))

        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if user:
            flash("Email already exists!")
            cursor.close()
            conn.close()
            return redirect(url_for("register"))

        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

        cursor.execute(
            "INSERT INTO users(fullname, email, password) VALUES(%s,%s,%s)",
            (fullname, email, hashed_password.decode("utf-8"))
        )

        conn.commit()
        cursor.close()
        conn.close()

        flash("Registration successful! Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"].encode("utf-8")):
            session["user_id"] = user["id"]
            session["fullname"] = user["fullname"]
            session["email"] = user["email"]
            flash("Welcome back!")
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT COUNT(*) AS total FROM scans WHERE user_id=%s",
        (session["user_id"],)
    )
    total_scans = cursor.fetchone()["total"]

    cursor.execute(
        "SELECT id, product_name, verdict, created_at FROM scans "
        "WHERE user_id=%s ORDER BY created_at DESC LIMIT 3",
        (session["user_id"],)
    )
    recent_scans = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "dashboard.html",
        fullname=session["fullname"],
        total_scans=total_scans,
        recent_scans=recent_scans
    )


# ---------------- UPLOAD ---------------- #

@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "food_image" not in request.files:
            flash("No file selected.")
            return redirect(url_for("upload"))

        file = request.files["food_image"]

        if file.filename == "":
            flash("Please choose an image.")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("Only JPG, JPEG and PNG files are allowed.")
            return redirect(url_for("upload"))

        ext = file.filename.rsplit(".", 1)[1].lower()
        filename = secure_filename(f"{uuid.uuid4().hex}.{ext}")
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)
        print(f"[upload] saved file to {filepath}")

        extracted_text = extract_text(filepath)
        print(f"[upload] OCR done, {len(extracted_text)} chars extracted")

        if not extracted_text or len(extracted_text.strip()) < 10:
            flash("Couldn't read that label clearly. Try a closer, well-lit photo of the ingredients list.")
            return redirect(url_for("upload"))

        analysis = analyze_ingredients(extracted_text)
        print("[upload] AI analysis done")

        _save_scan(
            user_id=session["user_id"],
            product_name=request.form.get("product_name") or "Scanned product",
            image_filename=filename,
            extracted_text=extracted_text,
            analysis=analysis
        )
        print("[upload] scan saved to DB")

        return render_template(
            "results.html",
            image=filename,
            extracted_text=extracted_text,
            analysis=analysis,
            systems_breakdown=group_by_body_system(analysis)
        )

    return render_template("upload.html")


# ---------------- MANUAL ENTRY ---------------- #

@app.route("/manual-entry", methods=["GET", "POST"])
@login_required
def manual_entry():
    if request.method == "POST":
        ingredients_text = request.form.get("ingredients", "").strip()

        if not ingredients_text:
            flash("Please paste or type the ingredients list.")
            return redirect(url_for("manual_entry"))

        analysis = analyze_ingredients(ingredients_text)

        _save_scan(
            user_id=session["user_id"],
            product_name=request.form.get("product_name") or "Manual entry",
            image_filename=None,
            extracted_text=ingredients_text,
            analysis=analysis
        )

        return render_template(
            "results.html",
            image=None,
            extracted_text=ingredients_text,
            analysis=analysis,
            systems_breakdown=group_by_body_system(analysis)
        )

    return render_template("manual_entry.html")


def _save_scan(user_id, product_name, image_filename, extracted_text, analysis):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scans (user_id, product_name, image_filename, extracted_text, verdict, analysis_json) "
        "VALUES (%s,%s,%s,%s,%s,%s)",
        (
            user_id,
            product_name,
            image_filename,
            extracted_text,
            analysis.get("overall_verdict", "Unknown"),
            json.dumps(analysis)
        )
    )
    conn.commit()
    cursor.close()
    conn.close()


# ---------------- HISTORY ---------------- #

@app.route("/history")
@login_required
def history():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT id, product_name, image_filename, verdict, created_at FROM scans "
        "WHERE user_id=%s ORDER BY created_at DESC",
        (session["user_id"],)
    )
    scans = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("history.html", scans=scans)


@app.route("/history/<int:scan_id>")
@login_required
def scan_detail(scan_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT * FROM scans WHERE id=%s AND user_id=%s",
        (scan_id, session["user_id"])
    )
    scan = cursor.fetchone()
    cursor.close()
    conn.close()

    if not scan:
        flash("Scan not found.")
        return redirect(url_for("history"))

    analysis = json.loads(scan["analysis_json"])

    return render_template(
        "results.html",
        image=scan["image_filename"],
        extracted_text=scan["extracted_text"],
        analysis=analysis,
        systems_breakdown=group_by_body_system(analysis)
    )


# ---------------- COMPARE PRODUCTS ---------------- #

@app.route("/compare", methods=["GET", "POST"])
@login_required
def compare_products():
    """Compare two saved product analyses belonging to the logged-in user."""

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, product_name, image_filename, verdict,
               extracted_text, analysis_json, created_at
        FROM scans
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (session["user_id"],)
    )

    scans = cursor.fetchall()
    cursor.close()
    conn.close()

    selected_a = request.values.get("product_a", type=int)
    selected_b = request.values.get("product_b", type=int)

    product_a = None
    product_b = None
    comparison = None

    # Only compare products owned by this user.
    scan_by_id = {scan["id"]: scan for scan in scans}

    if (
        selected_a in scan_by_id
        and selected_b in scan_by_id
        and selected_a != selected_b
    ):
        product_a = scan_by_id[selected_a]
        product_b = scan_by_id[selected_b]

        try:
            analysis_a = json.loads(
                product_a.get("analysis_json") or "{}"
            )
        except (TypeError, json.JSONDecodeError):
            analysis_a = {}

        try:
            analysis_b = json.loads(
                product_b.get("analysis_json") or "{}"
            )
        except (TypeError, json.JSONDecodeError):
            analysis_b = {}

        # Extract ingredient names from saved analyses.
        def get_ingredient_names(analysis):
            items = analysis.get("ingredients", [])

            if not isinstance(items, list):
                return {}

            return {
                item["name"].strip().casefold(): item["name"].strip()
                for item in items
                if isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and item["name"].strip()
            }

        ingredients_a = get_ingredient_names(analysis_a)
        ingredients_b = get_ingredient_names(analysis_b)

        # Extract saved allergen lists.
        def get_allergens(analysis):
            items = analysis.get("allergens", [])

            if not isinstance(items, list):
                return {}

            return {
                str(item).strip().casefold(): str(item).strip()
                for item in items
                if str(item).strip()
            }

        allergens_a = get_allergens(analysis_a)
        allergens_b = get_allergens(analysis_b)

        # Read numeric scores if available.
        def get_score(analysis):
            value = analysis.get("score")

            try:
                return float(value) if value is not None else None
            except (ValueError, TypeError):
                return None

        score_a = get_score(analysis_a)
        score_b = get_score(analysis_b)

        # Do not invent a winner if score data is missing.
        if score_a is not None and score_b is not None:
            if score_a > score_b:
                better = product_a["product_name"]
                reason = (
                    "Product A has the higher saved FoodLens score. "
                    "Review the ingredients and allergens before deciding."
                )
            elif score_b > score_a:
                better = product_b["product_name"]
                reason = (
                    "Product B has the higher saved FoodLens score. "
                    "Review the ingredients and allergens before deciding."
                )
            else:
                better = "Both products have the same score"
                reason = (
                    "Compare their ingredients and allergens to "
                    "understand the differences."
                )
        else:
            better = "Score comparison unavailable"
            reason = (
                "A numeric score was not found in both saved analyses."
            )

        comparison = {
            "analysis_a": analysis_a,
            "analysis_b": analysis_b,
            "score_a": score_a,
            "score_b": score_b,

            "only_a": sorted(
                ingredients_a[key]
                for key in ingredients_a.keys() - ingredients_b.keys()
            ),
            "only_b": sorted(
                ingredients_b[key]
                for key in ingredients_b.keys() - ingredients_a.keys()
            ),
            "shared": sorted(
                ingredients_a[key]
                for key in ingredients_a.keys() & ingredients_b.keys()
            ),

            "allergens_a": sorted(allergens_a.values()),
            "allergens_b": sorted(allergens_b.values()),
            "allergens_shared": sorted(
                allergens_a[key]
                for key in allergens_a.keys() & allergens_b.keys()
            ),

            "better": better,
            "reason": reason,
        }

    elif selected_a and selected_b and selected_a == selected_b:
        flash("Please select two different products.")

    return render_template(
        "compare.html",
        scans=scans,
        product_a=product_a,
        product_b=product_b,
        selected_a=selected_a,
        selected_b=selected_b,
        comparison=comparison,
    )

# ---------------- LOGOUT ---------------- #

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for("login"))


# ---------------- RUN APP ---------------- #

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)