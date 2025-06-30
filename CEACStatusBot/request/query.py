import requests
from bs4 import BeautifulSoup
import time

from CEACStatusBot.captcha import CaptchaHandle, OnnxCaptchaHandle

def query_status(application_num, captchaHandle: CaptchaHandle = OnnxCaptchaHandle("captcha.onnx")):
    isSuccess = False
    failCount = 0
    ROOT = "https://ceac.state.gov"
    session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html,application/xhtml+xml",
        "Connection": "keep-alive",
        "Host": "ceac.state.gov",
    }

    while not isSuccess and failCount < 5:
        failCount += 1

        try:
            r = session.get(f"{ROOT}/ceacstattracker/status.aspx?App=IV", headers=headers)
        except Exception as e:
            print("Connection error:", e)
            continue

        soup = BeautifulSoup(r.text, features="lxml")
        captcha = soup.find("img", id="c_status_ctl00_contentplaceholder1_defaultcaptcha_CaptchaImage")
        if not captcha:
            continue

        image_url = ROOT + captcha["src"]
        img_resp = session.get(image_url)
        captcha_num = captchaHandle.solve(img_resp.content)

        def update_field(name):
            tag = soup.find("input", {"name": name})
            return tag["value"] if tag else ""

        data = {
            "ctl00$ToolkitScriptManager1": "ctl00$ContentPlaceHolder1$UpdatePanel1|ctl00$ContentPlaceHolder1$btnSubmit",
            "__EVENTTARGET": "ctl00$ContentPlaceHolder1$btnSubmit",
            "__EVENTARGUMENT": "",
            "__LASTFOCUS": "",
            "__VIEWSTATE": update_field("__VIEWSTATE"),
            "__VIEWSTATEGENERATOR": update_field("__VIEWSTATEGENERATOR"),
            "__VIEWSTATEENCRYPTED": "",
            "ctl00$ContentPlaceHolder1$Visa_Application_Type": "IV",
            "ctl00$ContentPlaceHolder1$Location_Dropdown": "All",  # أو حذفه عند الحاجة
            "ctl00$ContentPlaceHolder1$Visa_Case_Number": application_num,
            "ctl00$ContentPlaceHolder1$Captcha": captcha_num,
            "LBD_VCID_c_status_ctl00_contentplaceholder1_defaultcaptcha": update_field("LBD_VCID_c_status_ctl00_contentplaceholder1_defaultcaptcha"),
            "LBD_BackWorkaround_c_status_ctl00_contentplaceholder1_defaultcaptcha": "1",
            "__ASYNCPOST": "true",
        }

        try:
            r = session.post(f"{ROOT}/ceacstattracker/status.aspx?App=IV", headers=headers, data=data)
        except Exception as e:
            print("POST error:", e)
            continue

        soup = BeautifulSoup(r.text, features="lxml")
        status_tag = soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatus")
        if not status_tag:
            continue  # غالبًا الكابتشا خطأ

        try:
            result = {
                "success": True,
                "time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "visa_type": soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblCaseTitle").text.strip(),
                "status": status_tag.text.strip(),
                "case_created": soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblSubmitDate").text.strip(),
                "case_last_updated": soup.find("span", id="ctl00_ContentPlaceHolder1_ucApplicationStatusView_lblStatusDate").text.strip(),
                "description": "",  # لا يوجد حقل لوصف الحالة
                "application_num": application_num,
                "application_num_origin": application_num
            }
            isSuccess = True
        except Exception as e:
            print("Parsing error:", e)
            continue

    if not isSuccess:
        return {"success": False}
    return result