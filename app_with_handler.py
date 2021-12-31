
#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import os
import sys
import tempfile
import datetime
from argparse import ArgumentParser
from flask import Flask, request, abort, send_from_directory, send_file
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageMessage, StickerSendMessage, VideoMessage,
    ImageSendMessage, TemplateSendMessage,  ButtonsTemplate, MessageAction
)
from linebot.models.events import (UnsendEvent)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'image')
other_tmp_path = os.path.join(os.path.dirname(__file__), 'otherimage')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'upimage')
path = os.path.join(os.path.dirname(__file__), 'log.txt')
otherpath = os.path.join(os.path.dirname(__file__), 'others.txt')
unsend_log = os.path.join(os.path.dirname(__file__), 'unsends.txt')

#IP位置
url = ''
glink = ''
glink1 = ''


app = Flask(__name__)
#app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)
app.config['SECRET_KEY'] = os.getenv('LINE_SECRET_KEY', None)
if app.config['SECRET_KEY'] is None:
    print('Specify LINE_SECRET_KEY as environment variable.')
    sys.exit(1)
# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)
gid = ''

@app.route("/file/<filename>", methods=['GET', 'POST'])
@app.route("/file_pre/<filename>", methods=['GET', 'POST'])
def upfile(filename):
    return send_from_directory(static_tmp_path,
                               filename)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    testevent = (request.get_json())['events'][0]
    # get request body as text
    body = request.get_data(as_text=True)
    #print(body)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    finally:
        writelog(testevent)
    
    return 'OK'

@handler.add(MessageEvent, message=ImageMessage)
def message_image(event):
    if isinstance(event.message, ImageMessage):
        p = other_tmp_path
        if event.type == 'message':
            if event.source.type == 'group':
                if (event.source).group_id == gid:
                    p = static_tmp_path
        ext = 'jpg'
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(dir=p, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
            
        #dist_path = tempfile_path + "_" + event.message.id + '.' + ext
        dist_path = os.path.join(p, "image_" + event.message.id + '.' + ext)
        dist_name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)

@handler.add(MessageEvent, message=VideoMessage)
def message_video(event):
    if isinstance(event.message, VideoMessage):
        p = other_tmp_path
        if event.type == 'message':
            if event.source.type == 'group':
                if (event.source).group_id == gid:
                    p = static_tmp_path
        ext = 'mp4'
        message_content = line_bot_api.get_message_content(event.message.id)
        with tempfile.NamedTemporaryFile(dir=p, prefix=ext + '-', delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
            
        #dist_path = tempfile_path + "_" + event.message.id + '.' + ext
        dist_path = os.path.join(p, "video_" + event.message.id + '.' + ext)
        dist_name = os.path.basename(dist_path)
        os.rename(tempfile_path, dist_path)   

@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    try:
        if event.message.text[:5] == "!log " and len(event.message.text) > 5:
            remessage = log_message(event.message.text[5:])
            if remessage == "":
                line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="查無記錄")
                    )
                return
            if len(remessage) > 2000:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="記錄過多，請增加關鍵字")
                )
                return
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=remessage[:len(remessage)-1])
            )
            return
        if event.message.text[:8] == "!unsend " and len(event.message.text) > 8:
            remessage = log_message(event.message.text[8:],unsend_log)
            if remessage == "":
                line_bot_api.reply_message(
                        event.reply_token,
                        TextSendMessage(text="查無記錄")
                    )
                return
            if len(remessage) > 2000:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="記錄過多，請增加關鍵字")
                )
                return
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=remessage[:len(remessage)-1])
            )
            return

    except Exception as e:
        print(event.message.text)
        print(e)
    if event.message.text[:7] == '!image ' and len(event.message.text) > 7:
        fname = event.message.text[7:] + '.jpg'
        if os.path.isfile(os.path.join(static_tmp_path, fname)):
            image_message = ImageSendMessage(
            original_content_url = url + '/file/' + fname ,
            preview_image_url = url + '/file_pre/' + fname
            )
            line_bot_api.reply_message(
                event.reply_token,
                image_message
            )
        else:
            line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="無此圖片")
            )
        return
    if event.message.text == '!help':
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="!log 名字/時間/內容，以&分隔")
        )
        return
    if event.message.text == '^icebear':
        image_message = ImageSendMessage(
            original_content_url = glink,
            preview_image_url = glink
            )
        line_bot_api.reply_message(
            event.reply_token,
            image_message
            )
        return    
    if event.message.text == '^icebear1':
        image_message = ImageSendMessage(
            original_content_url = glink1,
            preview_image_url = glink1
            )
        line_bot_api.reply_message(
            event.reply_token,
            image_message
            )
        return

@handler.add(UnsendEvent)
def message_unsend(event):
    if event.type == 'unsend':
        if event.source.type == 'group':
            if (event.source).group_id == gid:
               msg = log_message((event.unsend).message_id)
               with open(unsend_log, 'a', encoding = 'utf8') as file:
                file.write("[" + str(datetime.datetime.now())[5:16] + "] 回收︰")
                file.write(msg)

'''
@handler.add(MemberJoinEvent)
def welcomMessgae(event):
    image_message = ImageSendMessage(
        original_content_url = "",
        preview_image_url = ""
        )
    line_bot_api.reply_message(
        event.reply_token,
        image_message
    )
'''
def writelog(testevent):
    p = otherpath
    if testevent['type'] == 'message':
        if testevent['source']['type'] == 'group':
            if testevent['source']['groupId'] == gid:
                p = path
    try:
        uid = testevent['source']['userId']
        profile = line_bot_api.get_group_member_profile(gid, uid,10)
        username = profile.display_name
        #username = "unknown"
    except KeyError:
        print(testevent['source'])
        username = "unknown"
        
    utext = ""
    try:
        if testevent['message']['type'] == 'text':
            utext = testevent['message']['text']
        elif testevent['message']['type'] == 'image':
            utext = 'image_'+testevent['message']['id'] 
        else:
            if testevent['message']['type'] != 'sticker':
                print(testevent['message'])
            utext = testevent['message']['type']
    except:
        print(testevent)
        return
        
    with open(p, 'a', encoding = 'utf8') as file:
        if p == otherpath:
            file.write("[" + testevent['source']['type'] + "] ")
        file.write("[" + str(datetime.datetime.now())[5:16] + "] ")
        file.write("[" +testevent['message']['id']  + "] ")
        file.write(username + " : " + utext + "\n")

def log_message(keyword,path = path):
    keywords = keyword.split("&",5)
    num = len(keywords)
    if num > 5:
        return "查詢關鍵字過多"
    with open(path, "r", encoding = 'utf8') as f: 
        searchlines = f.readlines()
    linelog = ""
    for i, line in enumerate(searchlines):
        j = 0
        flag = True
        while j < num:
            if keywords[j] not in line:
                flag = False
                break
            j+=1
        if "!log " in line:
            flag = False
        if flag:
            linelog += searchlines[i]
            k = 1
            while (i+k) < len(searchlines):
                if searchlines[i+k][0] != "[":
                    linelog += searchlines[i+k]
                    k+=1
                else:
                    break
        '''
        else:
            if keywords[0] in line: 
                linelog += searchlines[i]
                j = 1
                while j > 0:
                    try:
                        if searchlines[i+j][0] != "[":
                            linelog += searchlines[i+j]
                            j+=1
                        else:
                            break
                    except IndexError:
                        break
        '''
    return linelog

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()
    app.run(debug=options.debug, port=options.port)
