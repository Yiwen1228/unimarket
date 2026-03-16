import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# 必须先调用 get_asgi_application() 完成 Django 初始化，再导入依赖模型的模块
from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from market.routing import websocket_urlpatterns

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
