import pyautogui
import pytesseract
import time
import webbrowser
import pyperclip
from PIL import ImageOps, ImageEnhance
from rapidfuzz import fuzz
from collections import Counter
import json

# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

scan_delay = 5
google_load_time = 3

correct_answer_log = []

# === Helpers ===

def capture_single_area(name):
    print(f"Move mouse to TOP-LEFT of {name}. Press [Enter].")
    input()
    x1, y1 = pyautogui.position()
    print(f"Top-left ({x1}, {y1})")

    print(f"Move mouse to BOTTOM-RIGHT of {name}. Press [Enter].")
    input()
    x2, y2 = pyautogui.position()
    print(f"Bottom-right ({x2}, {y2})")

    width = x2 - x1
    height = y2 - y1
    if width <= 0 or height <= 0:
        print(f"❌ Invalid area for {name}. Exiting.")
        exit()
    return (x1, y1, width, height)

def enhance_image(image):
    grayscale = ImageOps.grayscale(image)
    contrast = ImageEnhance.Contrast(grayscale).enhance(4.0)
    inverted = ImageOps.invert(contrast)
    return inverted

def read_text(region):
    screenshot = pyautogui.screenshot(region=region)
    enhanced = enhance_image(screenshot)
    config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(enhanced, config=config)
    return text.strip()

def is_blooket_tab_icon(region):
    icon_img = pyautogui.screenshot(region=region)
    pixels = icon_img.getcolors(icon_img.width * icon_img.height)

    if not pixels:
        return False

    # Blooket icon typically has teal/blue-green and white
    matches = [color for count, color in pixels
               if color[0] in range(30, 100) and color[1] in range(150, 255) and color[2] in range(180, 255)]

    print(f"🎨 Detected matching colors: {len(matches)}")
    return len(matches) >= 3

def google_search(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    time.sleep(google_load_time)

def find_correct_answer(answers, question_text):
    google_screenshot = pyautogui.screenshot()
    enhanced_google = enhance_image(google_screenshot)
    config = r'--oem 3 --psm 6'
    google_text = pytesseract.image_to_string(enhanced_google, config=config).lower()

    best_score = 0
    best_indices = []

    for idx, ans in enumerate(answers, start=1):
        ans_lower = ans.lower()
        score = fuzz.partial_ratio(ans_lower, google_text)
        print(f"🔎 Matching '{ans}' -> Score: {score}")

        if score > best_score:
            best_score = score
            best_indices = [idx]
        elif score == best_score:
            best_indices.append(idx)

    if best_score >= 60 and best_indices:
        best_idx = best_indices[0]
        print(f"🎯 Best match: Answer #{best_idx} with score {best_score}")

        correct_answer_log.append({
            "question": question_text,
            "answer": answers[best_idx - 1],
            "score": best_score
        })

        return best_idx
    else:
        print("❌ No good match found.")
        return None

def click_answer(idx, answer_positions):
    try:
        x, y = answer_positions[idx]
        print(f"🖱 Clicking answer #{idx} at ({x}, {y})")
        pyautogui.moveTo(x, y, duration=0.2)
        pyautogui.click()
    except Exception as e:
        print(f"❌ Error clicking: {e}")

def save_log():
    with open("correct_answers_log.json", "w") as f:
        json.dump(correct_answer_log, f, indent=2)
    print("📝 Answer log saved to correct_answers_log.json")

# === Main ===

def main():
    print("🚀 Blooket AutoPlayer Starting...")

    tab_icon_area = capture_single_area("Tab Icon (Blooket favicon)")
    question_area = capture_single_area("Question")
    answer_areas = []
    answer_positions = {}

    for i in range(1, 5):
        area = capture_single_area(f"Answer {i}")
        answer_areas.append(area)
        x, y, w, h = area
        answer_positions[i] = (x + w // 2, y + h // 2)

    while True:
        print("\nWaiting for next scan...")
        time.sleep(scan_delay)

        print("🧭 Checking favicon for Blooket tab...")
        if not is_blooket_tab_icon(tab_icon_area):
            print("❌ Not on Blooket. Closing tab...")
            pyautogui.hotkey('command', 'w')
            time.sleep(1)
            continue

        print("🔎 Reading question and answers...")
        question_text = read_text(question_area)
        answers_text = [read_text(area) for area in answer_areas]

        print(f"\n📖 Question: {question_text}")
        print(f"🧩 Answers: {answers_text}")

        if len(question_text.strip()) == 0 or any(len(ans.strip()) == 0 for ans in answers_text):
            print("❌ Missing text. Skipping...")
            continue

        pyperclip.copy(question_text)
        google_search(question_text)

        correct_idx = find_correct_answer(answers_text, question_text)

        try:
            time.sleep(0.5)
            time.sleep(1)  # Wait before closing to let Google fully load and refocus
            pyautogui.hotkey('command', 'w')  # Close Google tab
            print("🗂 Closed Google tab.")
            time.sleep(1)
        except Exception as e:
            print(f"⚠️ Couldn't close tab: {e}")

        if correct_idx:
            click_answer(correct_idx, answer_positions)
            time.sleep(2)
        else:
            print("❌ No matching answer found.")

        save_log()

if __name__ == "__main__":
    main()
