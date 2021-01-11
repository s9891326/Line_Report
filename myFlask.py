# from flask import Flask, request, abort
#
# from linebot import (
#     LineBotApi, WebhookHandler
# )
# from linebot.exceptions import (
#     InvalidSignatureError
# )
# from linebot.models import (
#     MessageEvent, TextMessage, TextSendMessage
# )
#
#
# app = Flask(__name__)
#
# access_token = "cBww7Ih93+0MGE7x7DJw1Fx9THAzvqXnZzzwY5CQ+ewI405qF94SJrwoUomTOxNbiEqOlDazjdpFzLOwdkboiK69aT9O3t7a9epgbTQ5e7/1RWeapmdT4bOMduBHmIPgA0w7SxPG8okkBRciuLtPvwdB04t89/1O/w1cDnyilFU="
# client_secret = "7c97bed9561b49b335895778a9c71380"
#
# line_bot_api = LineBotApi(client_secret)
# handler = WebhookHandler(access_token)
#
#
# @app.route("/callback", methods=['POST'])
# def callback():
#     # get X-Line-Signature header value
#     signature = request.headers['X-Line-Signature']
#
#     # get request body as text
#     body = request.get_data(as_text=True)
#     app.logger.info("Request body: " + body)
#
#     # handle webhook body
#     try:
#         handler.handle(body, signature)
#     except InvalidSignatureError:
#         abort(400)
#
#     return 'OK'
#
#
# @handler.add(MessageEvent, message=TextMessage)
# def handle_message(event):
#     line_bot_api.reply_message(
#         event.reply_token,
#         TextSendMessage(text=event.message.text))
#
#
# if __name__ == "__main__":
#     app.run()