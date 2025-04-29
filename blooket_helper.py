import pyautogui
import pytesseract
import time
import webbrowser
import pyperclip
from PIL import ImageOps, ImageEnhance
from rapidfuzz import fuzz
from collections import Counter

# Tesseract OCR path
pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"

scan_delay = 5
google_load_time = 3

# Helper Functions
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

def google_search(query):
    url = f"https://www.google.com/search?q={query}"
    webbrowser.open(url)
    time.sleep(google_load_time)

def find_correct_answer(answers):
    google_screenshot = pyautogui.screenshot()
    enhanced_google = enhance_image(google_screenshot)
    config = r'--oem 3 --psm 6'
    google_text = pytesseract.image_to_string(enhanced_google, config=config).lower()

    best_score = 0
    best_idx = None

    for idx, ans in enumerate(answers, start=1):
        ans_lower = ans.lower()
        score = fuzz.partial_ratio(ans_lower, google_text)
        print(f"🔎 Matching '{ans}' -> Score: {score}")

        if score > best_score:
            best_score = score
            best_idx = idx

    if best_score >= 60:  # You can adjust the threshold if needed
        print(f"🎯 Best match: Answer #{best_idx} with score {best_score}")
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

def main():
    print("🚀 Blooket 5-Capture AutoPlayer Starting...")

    # Step 1: Capture regions
    question_area = capture_single_area("Question")
    answer_areas = []
    answer_positions = {}

    for i in range(1, 5):
        area = capture_single_area(f"Answer {i}")
        answer_areas.append(area)
        # Save center position for clicking
        x, y, w, h = area
        center_x = x + w // 2
        center_y = y + h // 2
        answer_positions[i] = (center_x, center_y)

    while True:
        print("\nWaiting for next scan...")
        time.sleep(scan_delay)

        print("🔎 Scanning...")

        question_text = read_text(question_area)
        answers_text = [read_text(area) for area in answer_areas]

        print(f"\n📖 Question: {question_text}")
        print(f"🧩 Answers: {answers_text}")

        if len(question_text.strip()) == 0 or any(len(ans.strip()) == 0 for ans in answers_text):
            print("❌ Missing text. Skipping...")
            continue

        pyperclip.copy(question_text)
        google_search(question_text)

        correct_idx = find_correct_answer(answers_text)

        pyautogui.hotkey('command', 'w')  # Close Google tab
        time.sleep(0.5)

        if correct_idx:
            click_answer(correct_idx, answer_positions)
        else:
            print("❌ No matching answer found.")
        if correct_idx:
            click_answer(correct_idx, answer_positions)
            time.sleep(2)  # Let the green/red screen load
        else:
            print("❌ No matching answer found.")

if __name__ == "__main__":
    main()