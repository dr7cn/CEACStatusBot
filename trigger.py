import os
from CEACStatusBot import NotificationManager, TelegramNotificationHandle

try:
    NUMBER = os.environ["NUMBER"]
    notificationManager = NotificationManager(NUMBER)
except KeyError:
    print("NUMBER is missing in environment variables")
    exit(1)

try:
    BOT_TOKEN = os.environ["TG_BOT_TOKEN"]
    CHAT_ID = os.environ["TG_CHAT_ID"]
    if BOT_TOKEN and CHAT_ID:
        tgNotif = TelegramNotificationHandle(BOT_TOKEN, CHAT_ID)
        notificationManager.addHandle(tgNotif)
except KeyError:
    print("Telegram bot notification config error")
    exit(1)

notificationManager.send()