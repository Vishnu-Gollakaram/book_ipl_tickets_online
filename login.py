import time
import random
import smtplib
import string
import tkinter as tk
from tkinter import simpledialog, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.message import EmailMessage
import requests

# Remote admin list URL from GitHub
ADMIN_LIST_URL = "https://raw.githubusercontent.com/Vishnu-Gollakaram/book_ipl_tickets_online/main/admins.txt"

# Function to generate a random access token
def generate_token(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

# Function to fetch the latest admin list from GitHub
def get_admins():
    try:
        response = requests.get(ADMIN_LIST_URL)
        if response.status_code == 200:
            return list(set(email.strip().lower() for email in response.text.split("\n") if email.strip()))
        else:
            print("⚠️ Failed to fetch admin list. Using last known admins.")
            return list()
    except Exception as e:
        print(f"❌ Error fetching admin list: {e}")
        return list()

# Fetch latest admin list
ADMINS = get_admins()
print(f"📜 Current Admins: {ADMINS}")


# Generate a token and send it via email
ACCESS_TOKEN = generate_token()
# send_email(ACCESS_TOKEN)

sender_email = "vgollakaram3@gmail.com"
app_password = "vgxu ygco rvlv tdeu"

receiver_email = ", ".join(ADMINS)
subject = f"API Token email from Booking app {datetime.now()}"
body = f"""
API is as Below:
{ACCESS_TOKEN}
"""

# Create email message
msg = MIMEText(body)
msg["Subject"] = subject
msg["From"] = sender_email
msg["To"] = receiver_email

try:
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()  # Secure connection
        server.login(sender_email, app_password)
        server.sendmail(sender_email, ADMINS, msg.as_string())
        print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")

# Initialize Tkinter (For Dialog Boxes)
root = tk.Tk()
root.withdraw()  # Hide the main window

# Ask user for Approval Token
user_token = simpledialog.askstring("Approval Required", "Enter the access token from creator!")
if user_token != ACCESS_TOKEN:
    messagebox.showerror("Access Denied", "Invalid token! You are not authorized to run this script.")
    exit()

# Ask user for Mobile Number
mobile_number = simpledialog.askstring("Mobile Number", "Enter your mobile number:")
if not mobile_number:
    messagebox.showerror("Error", "Mobile number is required!")
    exit()

# Ask user for Home Team
home_team = simpledialog.askstring("Home Team", "Enter the Home Team name:")
if not home_team:
    messagebox.showerror("Error", "Home Team is required!")
    exit()

# Ask user for Opponent Team
opponent_team = simpledialog.askstring("Opponent Team", "Enter the Opponent Team name:")
if not opponent_team:
    messagebox.showerror("Error", "Opponent Team is required!")
    exit()

# Set up the WebDriver
driver = webdriver.Chrome()

retries = 10000000000000000  # Maximum retry attempts
delay = 2  # Initial wait time in seconds

try:
    # Open the login page
    driver.get("https://www.district.in/users/login")

    # Wait for the mobile input field to be present
    mobile_input = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.NAME, "mobileNumber"))
    )

    # Enter the mobile number
    mobile_input.send_keys(mobile_number)
    print("Mobile number entered.")

    # Wait for the 'Continue' button and click it
    continue_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Continue')]"))
    )
    continue_button.click()
    print("Clicked on Continue.")

    WebDriverWait(driver, 60).until(
        EC.url_to_be("https://www.district.in/")
    )

    print("Login successful! Page navigated to:", driver.current_url)

    for attempt in range(retries):
        try:
            print(f"Attempt {attempt + 1}: Checking for the close button...")
            close_button = WebDriverWait(driver, delay).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close ad']"))
            )
            close_button.click()
            print("Interstitial ad closed.")
            break  # Exit loop once clicked successfully
        except Exception as e:
            print(f"Close button not found. Retrying in {delay} seconds...")
            time.sleep(delay)
            delay *= 2  # Exponential backoff: 2s → 4s → 8s...
    else:
        print("Pop-up close button not found after multiple attempts. Continuing...")

    for attempt in range(retries):
        try:
            match_xpath = (
                "//div[@role='region' and "
                f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{home_team}') and "
                f"contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{opponent_team}')]"
                "//a"
            )

            match_element = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, match_xpath))
            )
            print("Match element found. Clicking on match element...")
            match_element.click()
            print("Navigated to the match details page.")

            # Wait until the URL contains "/event"
            WebDriverWait(driver, 20).until(lambda d: "/event" in d.current_url)

            # Get the current URL
            current_url = driver.current_url
            print("Event Page Loaded:", current_url)

            # Replace "/event" with "/buy-page"
            new_url = current_url.replace("/event", "/buy-page")
            new_url = new_url.replace("district.in/", "district.in/event/")
            print("Navigating to:", new_url)

            # Open the new page
            driver.get(new_url)

            WebDriverWait(driver, 30).until(EC.url_contains("/buy-page/shows/"))
            print("Redirected to:", driver.current_url)

            time.sleep(600)
            break
        except Exception as e:
            print(f"Exception occurred: {e}, retrying...")
            time.sleep(0.01)

except Exception as e:
    print("An error occurred:", e)

finally:
    input("Press Enter to close the browser...")
    driver.quit()
