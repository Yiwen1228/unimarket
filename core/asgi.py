import os
from django.core.asgi import get_asgi_application

# 引入 Channels 的路由和认证模块（必须确保已安装 channels 库）
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

# 这里会标红报错是正常的，因为我们还没建 routing.py，下一步建
from market.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 1. 初始化基础的 Django HTTP 异步应用
django_asgi_app = get_asgi_application()

# 2. 真正的核心：重写 application，让它成为协议路由器
application = ProtocolTypeRouter({
    # 如果是普通的网页刷新、AJAX 请求，统统交给传统的 Django 处理，保证旧代码零冲突
    "http": django_asgi_app,
    
    # 如果是 WebSocket 聊天请求，包裹上 Session 身份认证，导向专用的 WebSocket 路由池
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
