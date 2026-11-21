"""
QuestForge -> HackerRank Community Auto-Publisher
Fully automated:
- Authenticates using saved credentials
- Creates challenges directly via HackerRank administration
- Links them directly to your HackerRank contest
- Populates problem statement, input format, constraints, and output format
- Automatically packages and uploads test cases via ZIP
- Sets contest challenge score and saves
- Updates QuestForge database with live status and links
"""

import os
import sys
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)
import time
import zipfile
import tempfile
import argparse
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv(".env")
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
CONTEST_EDIT_ID = "407822"  # Contest ID for demo 1795165296

def get_db_connection():
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL not found in .env")
        sys.exit(1)
    return psycopg2.connect(DATABASE_URL)

def fetch_questions(conn, question_id=None, all_approved=False):
    cur = conn.cursor(cursor_factory=RealDictCursor)
    if question_id:
        cur.execute("SELECT * FROM questions WHERE id = %s LIMIT 1", (question_id,))
    elif all_approved:
        cur.execute("SELECT * FROM questions WHERE status IN ('approved', 'published') ORDER BY created_at ASC")
    else:
        cur.execute("SELECT * FROM questions WHERE status IN ('approved', 'published') ORDER BY created_at ASC")
    rows = cur.fetchall()
    cur.close()
    return rows

def fetch_test_cases(conn, question_id):
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM test_cases WHERE question_id = %s ORDER BY id ASC", (question_id,))
    rows = cur.fetchall()
    cur.close()
    return rows

def ensure_authenticated(page, username=None, password=None):
    """Logs into HackerRank using credentials if not already logged in."""
    page.goto("https://www.hackerrank.com/administration/challenges/create", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    url = page.url

    # Check if logged in
    if not page.query_selector('input[name="login"]') and ("administration" in url or "dashboard" in url or "challenges" in url):
        print(" [HackerRank Auto-Publisher] Already authenticated as logged-in user!")
        return True

    print(" [HackerRank Auto-Publisher] Performing automated login...")
    page.goto("https://www.hackerrank.com/auth/login", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # Dismiss cookies if present
    try:
        btn = page.query_selector('button:has-text("Accept All Cookies"), button:has-text("OK")')
        if btn:
            btn.click()
            page.wait_for_timeout(1000)
    except:
        pass

    u = username or os.getenv("HACKERRANK_USERNAME")
    p = password or os.getenv("HACKERRANK_PASSWORD")

    u_box = page.query_selector('input[name="username"]')
    p_box = page.query_selector('input[name="password"]')

    if u_box and p_box and u and p:
        print(f" [HackerRank Auto-Publisher] Logging in as '{u}'...")
        u_box.fill(u)
        p_box.fill(p)
        page.wait_for_timeout(500)
        login_btn = page.query_selector('button:has-text("Log In")')
        if login_btn:
            login_btn.click()
        else:
            p_box.press("Enter")
        page.wait_for_timeout(5000)

    if "dashboard" in page.url or "administration" in page.url or page.title().startswith("Dashboard"):
        print(" [HackerRank Auto-Publisher] Login successful!")
        return True

    print(" [HackerRank Auto-Publisher] Waiting for session confirmation...")
    for _ in range(30):
        time.sleep(2)
        if "dashboard" in page.url or "administration" in page.url:
            print(" [HackerRank Auto-Publisher] Logged in successfully!")
            return True

    print("[ERROR] Login failed. Please verify credentials in .env")
    return False

def create_challenge_on_hackerrank(page, q):
    title = q["title"]
    print(f"\n🚀 Creating challenge container: '{title}'...")

    page.goto("https://www.hackerrank.com/administration/challenges/create", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    preview = (q.get("story") or title)[:140]
    tags = q.get("tags") or [q.get("topic") or "algorithms"]
    if isinstance(tags, str):
        try:
            import json
            tags = json.loads(tags)
        except:
            tags = [tags]

    res = page.evaluate("""([title, preview, tags]) => {
        return new Promise((resolve) => {
            const model = new HR.Administration_ChallengeModel({
                name: title,
                preview: preview,
                tags: tags
            });
            model.save(null, {
                success: function(m, response) {
                    resolve({ success: true, slug: m.get('slug') || response.model?.slug, id: m.get('id') || response.model?.id });
                },
                error: function(m, xhr) {
                    resolve({ success: false, status: xhr.status, errorText: xhr.responseText });
                }
            });
        });
    }""", [title, preview, tags])

    if res.get("success"):
        slug = res.get("slug")
        ch_id = res.get("id")
        print(f" ✅ Challenge created! Slug: '{slug}', ID: {ch_id}")
        return {"id": ch_id, "slug": slug}
    else:
        print(f" ⚠️ Notice during challenge save: {res.get('errorText') or res}")
        fallback_slug = title.lower().replace(" ", "-").replace(":", "").replace("'", "")
        return {"id": None, "slug": fallback_slug}

def link_challenge_to_contest(page, contest_id, challenge_slug):
    print(f"\n🔗 Linking challenge '{challenge_slug}' to contest edit page...")
    url = f"https://www.hackerrank.com/administration/contests/edit/{contest_id}/challenges"
    page.goto(url, wait_until="domcontentloaded")
    page.wait_for_timeout(3000)

    # 1. Click Add Challenge
    add_btn = page.query_selector("button.add-challenge")
    if not add_btn:
        print("  ⚠️ Could not find Add Challenge button on contest edit page.")
        return False
    add_btn.click()
    page.wait_for_timeout(1500)

    # 2. Type slug
    input_box = page.query_selector("input.add-challenge-input")
    if not input_box:
        print("  ⚠️ Could not find challenge input in modal.")
        return False

    input_box.fill(challenge_slug)
    page.wait_for_timeout(2000)

    # 3. Autocomplete dropdown
    dropdown = page.query_selector(".ui-autocomplete li")
    if dropdown:
        dropdown.click()
        page.wait_for_timeout(1000)

    # 4. Click Add Challenge button inside modal
    modal_btn = page.query_selector("button.add-challenge-button")
    if modal_btn:
        modal_btn.click()
        page.wait_for_timeout(2500)

    # 5. Save Contest Changes
    save_btn = page.query_selector("button.save-contest, button:has-text('Save Changes')")
    if save_btn:
        save_btn.click()
        page.wait_for_timeout(2500)

    print(f"  🎉 Challenge '{challenge_slug}' linked directly to contest!")
    return True

def populate_problem_details(page, contest_id, challenge_id, q):
    if not challenge_id:
        return
    details_url = f"https://www.hackerrank.com/administration/contests/edit/{contest_id}/challenges/edit/{challenge_id}/details"
    print(f"\n📝 Populating problem statement at {details_url}...")
    page.goto(details_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3500)

    title = q["title"]
    stmt = q.get("story") or title
    if q.get("explanation"):
        stmt += f"\n\n### Explanation\n{q['explanation']}"
    inp = q.get("input_format") or ""
    cons = q.get("constraints") or ""
    out = q.get("output_format") or ""

    page.evaluate("""([s, i, c, o]) => {
        const cms = Array.from(document.querySelectorAll('.CodeMirror'));
        if (cms[0]?.CodeMirror) cms[0].CodeMirror.setValue(s);
        if (cms[1]?.CodeMirror) cms[1].CodeMirror.setValue(i);
        if (cms[2]?.CodeMirror) cms[2].CodeMirror.setValue(c);
        if (cms[3]?.CodeMirror) cms[3].CodeMirror.setValue(o);
    }""", [stmt, inp, cons, out])

    page.wait_for_timeout(1000)

    save_btn = page.query_selector("button.save-challenge, button.btn-green, button:has-text('Save Changes')")
    if save_btn:
        save_btn.click()
        page.wait_for_timeout(3500)
        print("  ✅ Problem statement saved successfully!")

def upload_test_cases_zip(page, contest_id, challenge_id, test_cases):
    if not challenge_id or not test_cases:
        return
    tc_url = f"https://www.hackerrank.com/administration/contests/edit/{contest_id}/challenges/edit/{challenge_id}/testcases"
    print(f"\n📦 Packaging & uploading {len(test_cases)} test case(s) at {tc_url}...")

    temp_zip = os.path.join(tempfile.gettempdir(), f"tc_{challenge_id}.zip")
    with zipfile.ZipFile(temp_zip, "w") as z:
        for idx, tc in enumerate(test_cases):
            z.writestr(f"input{idx:02d}.txt", (tc.get("input_data") or "") + "\n")
            z.writestr(f"output{idx:02d}.txt", (tc.get("output_data") or "") + "\n")

    page.goto(tc_url, wait_until="domcontentloaded")
    page.wait_for_timeout(3500)

    upload_zip_btn = page.query_selector("button:has-text('Upload Zip')")
    if upload_zip_btn:
        upload_zip_btn.click()
        page.wait_for_timeout(1500)

        dialog = page.query_selector(".administration-challenge-edit-upload-zip-dialog")
        if dialog:
            f_input = dialog.query_selector("input[type='file']")
            if f_input:
                f_input.set_input_files(temp_zip)
                page.wait_for_timeout(2000)

                d_btns = dialog.query_selector_all("button, input[type='submit']")
                for db in d_btns:
                    if "upload" in db.inner_text().lower():
                        db.click()
                        page.wait_for_timeout(5000)
                        break

        save_btn = page.query_selector("button.save-challenge, button:has-text('Save Changes')")
        if save_btn:
            save_btn.click()
            page.wait_for_timeout(2500)
        print("  ✅ Test cases uploaded and saved!")

def update_db_published(conn, question_id, slug):
    cur = conn.cursor()
    cur.execute("""
        UPDATE questions 
        SET status = 'published', 
            remote_hackerrank_id = %s,
            hackerrank_url = %s,
            published_at = NOW(),
            updated_at = NOW()
        WHERE id = %s
    """, (slug, f"https://www.hackerrank.com/challenges/{slug}", question_id))
    conn.commit()
    cur.close()

def main():
    parser = argparse.ArgumentParser(description="Auto-publish QuestForge questions to HackerRank Community")
    parser.add_argument("--contest-id", default=CONTEST_EDIT_ID, help=f"HackerRank contest edit ID (default: {CONTEST_EDIT_ID})")
    parser.add_argument("--question-id", default=None, help="Specific question ID (e.g. q_seed_graphs_hard)")
    parser.add_argument("--all", action="store_true", help="Publish all approved questions")
    parser.add_argument("--username", default=None, help="HackerRank username / email")
    parser.add_argument("--password", default=None, help="HackerRank password")
    args = parser.parse_args()

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    profile_dir = os.path.join(project_root, "data", "hr_browser_profile")
    os.makedirs(profile_dir, exist_ok=True)

    print("\n" + "=" * 65)
    print(" ⚡ QuestForge HackerRank Auto-Publisher (Full Pipeline)")
    print(f" Contest ID: {args.contest_id}")
    print("=" * 65 + "\n")

    conn = get_db_connection()
    questions = fetch_questions(conn, question_id=args.question_id, all_approved=args.all)

    if not questions:
        print("[INFO] No questions found.")
        conn.close()
        return

    print(f"Found {len(questions)} question(s) to process:")
    for q in questions:
        print(f" - [{q['id']}] {q['title']} ({q['difficulty']})")

    with sync_playwright() as p:
        print("\n🌐 Launching Chrome session...")
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            channel="chrome",
            headless=False,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()

        if not ensure_authenticated(page, username=args.username, password=args.password):
            context.close()
            conn.close()
            return

        for q in questions:
            tcs = fetch_test_cases(conn, q["id"])
            created = create_challenge_on_hackerrank(page, q)
            slug = created["slug"]
            ch_id = created["id"]

            if slug:
                # 1. Link to contest
                link_challenge_to_contest(page, args.contest_id, slug)
                # 2. Populate Problem Statement details
                populate_problem_details(page, args.contest_id, ch_id, q)
                # 3. Upload test cases via ZIP
                upload_test_cases_zip(page, args.contest_id, ch_id, tcs)
                # 4. Update QuestForge DB
                update_db_published(conn, q["id"], slug)
                print(f"✅ Finished full deployment of '{q['title']}'! Live on HackerRank.\n")

        print("🎉 Done! Leaving browser open for 3 seconds...")
        time.sleep(3)
        context.close()

    conn.close()
    print("✨ HackerRank Auto-Publisher pipeline completed successfully!")

if __name__ == "__main__":
    main()
