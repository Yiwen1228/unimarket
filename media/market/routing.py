# market/routing.py
from django.urls import re_path
# 假设 Yiwen 编写了一个 ChatConsumer 来处理 WebSocket 逻辑
from . import consumers 

websocket_urlpatterns = [
    # 使用正则表达式匹配房间号，这对应了你前端 JS 中的 ws/chat/${roomName}/
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]