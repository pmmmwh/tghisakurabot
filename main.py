# -*- coding: utf-8 -*-
import StringIO
import json
import logging
import random
import urllib
import urllib2
import re

# for sending images
from PIL import Image
import multipart

# standard app engine imports
from google.appengine.api import urlfetch
from google.appengine.ext import ndb
import webapp2

TOKEN = '216426614:AAF52e_8GegU4dmF_cbtrh9qHpZRvqg_bcY'

BASE_URL = 'https://api.telegram.org/bot' + TOKEN + '/'


# ================================

class EnableStatus(ndb.Model):
    # key name: str(chat_id)
    enabled = ndb.BooleanProperty(indexed=False, default=False)

# ================================

def setEnabled(chat_id, yes):
    es = EnableStatus.get_or_insert(str(chat_id))
    es.enabled = yes
    es.put()

def getEnabled(chat_id):
    es = EnableStatus.get_by_id(str(chat_id))
    if es:
        return es.enabled
    return False

# ================================

class MeHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getMe'))))


class GetUpdatesHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'getUpdates'))))


class SetWebhookHandler(webapp2.RequestHandler):
    def get(self):
        urlfetch.set_default_fetch_deadline(60)
        url = self.request.get('url')
        if url:
            self.response.write(json.dumps(json.load(urllib2.urlopen(BASE_URL + 'setWebhook', urllib.urlencode({'url': url})))))


class WebhookHandler(webapp2.RequestHandler):
    def post(self):
        urlfetch.set_default_fetch_deadline(60)
        body = json.loads(self.request.body)
        logging.info('request body:')
        logging.info(body)
        self.response.write(json.dumps(body))

        update_id = body['update_id']
        try:
            message = body['message']
        except:
            message = body['edited_message']
        message_id = message.get('message_id')
        date = message.get('date')
        text = message.get('text')
        fr = message.get('from')
        chat = message['chat']
        chat_id = chat['id']
        senderid = fr.get('username')
        senderfname = fr.get('first_name')

        if not text:
            logging.info('no text')
            return

        # message handles
        def reply(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                    'reply_to_message_id': str(message_id),
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                    ('reply_to_message_id', str(message_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        def say(msg=None, img=None):
            if msg:
                resp = urllib2.urlopen(BASE_URL + 'sendMessage', urllib.urlencode({
                    'chat_id': str(chat_id),
                    'text': msg.encode('utf-8'),
                    'disable_web_page_preview': 'true',
                })).read()
            elif img:
                resp = multipart.post_multipart(BASE_URL + 'sendPhoto', [
                    ('chat_id', str(chat_id)),
                ], [
                    ('photo', 'image.jpg', img),
                ])
            else:
                logging.error('no msg or img specified')
                resp = None

            logging.info('send response:')
            logging.info(resp)

        # general commands
        if text.startswith('/'):
            if re.search('^/start@hisakurabot', text, re.I) is not None:
                say('Bot enabled')
                setEnabled(chat_id, True)
            elif re.search('^/stop@hisakurabot', text, re.I) is not None:
                say('Bot disabled')
                setEnabled(chat_id, False)
            elif re.search('^/help@hisakurabot', text, re.I) is not None:
                say(u'help - 幫助列表\nstart - 起動小櫻花機械人\nstop - 停止小櫻花機械人\neat - 對小櫻花餵食 (e.g. 八腳)\nkill - 命令小櫻花把某某的頭咬掉 (e.g. 老細)\nannounce - 顯示群組公告\ngetchatid - 獲取現時聊天室的ID (Debug用)')

            # bot commands
            if getEnabled(chat_id):
                if re.search('^/eat', text, re.I) is not None:
                    replymsg = message.get('reply_to_message')

                    if replymsg is not None:
                        replyuser = replymsg.get('from')
                        firstname = replyuser.get('first_name')
                        eatmsg = [u'原來 %s 挺好吃的呢...' %firstname, u'啊啊啊 %s 有毒(暈' %firstname, u'我才不要吃 %s 呢(吐' % firstname]
                        eatint = random.randint(0, 2)
                        say(u'%s' %eatmsg[eatint])
                    elif re.search(' LPC', text, re.I) is not None or re.search(' Lawson Power Cube', text, re.I) is not None:
                        eatmsg = [u'LPC裡面有大量XM啊～一下子就吃飽了！', u'啊啊啊身體都被XM充滿了啊啊啊啊！', u'LPC什麼的最喜歡了！(咬']
                        eatint = random.randint(0, 2)
                        say(u'%s' %eatmsg[eatint])
                    elif re.search(' me', text, re.I) is not None or re.search(' ' + senderid, text, re.I) is not None:
                        say(u'快給我LPC，你一點都不好吃！(嘔')
                    elif u'八腳' in text:
                        say(u'八腳很有用，你留著吧不要餵我吃了～')
                    elif ' ' in text:
                        say(u'我只吃LPC，其餘的通通不要 :P')
                    else:
                        say(u'求食物、求食物、求食物！ :X')
                elif re.search('^/kill', text, re.I) is not None:
                    replymsg = message.get('reply_to_message')

                    if replymsg is not None:
                        replyuser = replymsg.get('from')
                        firstname = replyuser.get('first_name')
                        killmsg = [u'你殺氣騰騰的是怎麼了？我殺了 %s 就是了...' % firstname, u'成功伏擊 %s ！' % firstname, u'刺殺 %s 失敗了...真可惜' % firstname, u'%s 舉起了中指防住了偶的攻擊(汗' % firstname]
                        killint = random.randint(0, 3)
                        say(u'%s' %killmsg[killint])
                    elif re.search(' me', text, re.I) is not None or re.search(' ' + senderid, text, re.I) is not None:
                        say(unicode(senderfname) + u' 想自殘麼？謝謝你的頭，拜拜囉(用力嚼')
                    elif ' ' in text:
                        player = text.split(" ", 1)
                        killmsg = [u'已把 %s 的頭咬掉(嚼嚼嚼...' % player[1], u'嗚啊！我沒咬中 %s 的頭...' % player[1]]
                        killint = random.randint(0,1)
                        say(u'%s' %killmsg[killint])
                    else:
                        say(unicode(senderfname) + u'，你想我咬誰呢 :P')
                elif re.search('^/announce', text, re.I) is not None:
                    if chat_id == -120095478:
                        say(u'群組公告：\n1. 櫻花 Chat Bot Beta 1.0 @HiSakuraBot')
                    elif chat_id == -1001057645178:
                        say(u'Bacon Pancaaaaaake!')
                    else:
                        say(u'本群組沒有設置公告！')
                elif re.search('^/getchatid', text, re.I) is not None:
                    say(str(chat_id))
            else:
            	if not getEnabled(chat_id):
                    logging.info('not enabled for chat_id {}'.format(chat_id))


app = webapp2.WSGIApplication([
    ('/me', MeHandler),
    ('/updates', GetUpdatesHandler),
    ('/set_webhook', SetWebhookHandler),
    ('/webhook', WebhookHandler),
], debug=True)
