import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatMessage


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        history = await self.get_history()
        for msg in history:
            await self.send(text_data=json.dumps({
                'message': msg['message'],
                'sender': msg['sender'],
                'role': msg['role'],
                'timestamp': msg['timestamp'],
                'history': True,
            }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        if data.get('type') == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_typing',
                    'sender': data.get('sender', 'Anonymous'),
                }
            )
            return

        message = data.get('message', '').strip()
        sender = data.get('sender', 'Anonymous')
        role = data.get('role', 'customer')
        product_id = data.get('productId')

        if not message:
            return

        ts = await self.save_message(sender, role, message, product_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'role': role,
                'timestamp': ts,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'role': event['role'],
            'timestamp': event.get('timestamp', ''),
        }))

    async def chat_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'sender': event['sender'],
        }))

    @database_sync_to_async
    def save_message(self, sender, role, message, product_id=None):
        kwargs = dict(
            room_name=self.room_name,
            sender=sender,
            role=role,
            message=message,
        )
        if product_id:
            try:
                kwargs['product_id'] = int(product_id)
            except (ValueError, TypeError):
                pass
        obj = ChatMessage.objects.create(**kwargs)
        return obj.timestamp.isoformat()

    @database_sync_to_async
    def get_history(self):
        msgs = ChatMessage.objects.filter(room_name=self.room_name).order_by('-timestamp')[:50]
        return [
            {
                'message': m.message,
                'sender': m.sender,
                'role': m.role,
                'timestamp': m.timestamp.isoformat(),
            }
            for m in reversed(msgs)
        ]
