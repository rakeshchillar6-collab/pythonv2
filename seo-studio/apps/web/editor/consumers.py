# editor/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync

class EditorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.post_id = self.scope['url_route']['kwargs']['post_id']
        self.room_group_name = f'editor_{self.post_id}'
        self.user = self.scope['user']

        if not self.user.is_authenticated:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Announce user's presence to the group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user': self.user.email
            }
        )

    async def disconnect(self, close_code):
        # Announce user's departure
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_leave',
                'user': self.user.email
            }
        )

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'lock_paragraph':
            # Broadcast the lock message to others in the group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'paragraph_locked',
                    'paragraph_id': data['paragraph_id'],
                    'user': self.user.email
                }
            )
        elif message_type == 'unlock_paragraph':
            # Broadcast the unlock message
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'paragraph_unlocked',
                    'paragraph_id': data['paragraph_id']
                }
            )

    # --- Handlers for group messages ---

    async def user_join(self, event):
        await self.send(text_data=json.dumps(event))

    async def user_leave(self, event):
        await self.send(text_data=json.dumps(event))

    async def paragraph_locked(self, event):
        # Don't send lock event back to the user who initiated it
        if self.user.email != event['user']:
            await self.send(text_data=json.dumps(event))

    async def paragraph_unlocked(self, event):
        await self.send(text_data=json.dumps(event))
