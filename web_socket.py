import asyncio
import json
import math
import websockets
import pytchat
import datetime

from peewee import DoesNotExist

from game import Game, gen_status_report, register_vote, gen_vote_report
from models import User, Vote, Country
from playhouse.shortcuts import model_to_dict


class WebsocketClient:
    def __init__(self, game: Game):
        self.game = game
        self.clients = set()

    async def notify_clients(self, report: dict) -> None:
        if self.clients:
            msg = json.dumps(report, ensure_ascii=False)  # Important for emojis!
            disconnected = set()
            for client in self.clients:
                try:
                    await client.send(msg)
                except:
                    disconnected.add(client)
            self.clients.difference_update(disconnected)

    async def handler(self, websocket):
        self.clients.add(websocket)
        try:
            report = gen_status_report()
            await websocket.send(json.dumps(report, ensure_ascii=False))
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)

    async def _process_message(self, c):
        msg = c.message.strip()
        if len(msg) < 2:
            return

        alpha2 = msg[:2].upper()
        try:
            country = Country.get(alpha2=alpha2)
        except DoesNotExist:
            print(f'{alpha2} is not a valid country code.')
            return

        # Force username to Python str and log for debugging
        username = str(c.author.name)
        print(f"Received username: {repr(username)}")

        user, created = User.get_or_create(
            user_id=c.author.channelId,
            defaults={
                "username": username,
                "channel_url": c.author.channelUrl,
                "image_url": c.author.imageUrl,
                "is_mod": c.author.isChatModerator,
            }
        )

        if not created:
            # Update values, force str, and log
            user.username = str(c.author.name)
            user.channel_url = str(c.author.channelUrl)
            user.image_url = str(c.author.imageUrl)
            user.is_mod = c.author.isChatModerator
            print(f"Saving user: id={user.user_id}, username={repr(user.username)}")
            user.save()
        else:
            print(f"Created user: id={user.user_id}, username={repr(user.username)}")

        vote = Vote.create(
            user=user,
            country=country,
            vote_count=1,
            points=100 + math.floor(user.leveling),
            timestamp=datetime.datetime.now(),
        )

        events = register_vote(vote)
        await self.notify_clients(gen_vote_report(vote, events))

    async def process_message(self, c, timeout=5):
        """Does not fry everything if processing fails"""
        try:
            await asyncio.wait_for(self._process_message(c), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"ERROR: Processing message '{c.message}' by {c.author.name} timed out after {timeout} seconds.")
            return
        except Exception as e:
            print(f"Exception while processing message '{c.message}': {e}")
            return
        print(f'Successfully evaluated {c.message} by {c.author.name}')

    async def chat_watcher(self, video_id):
        """Robustly watches chat, restarts pytchat session if it dies, with logging and auto-retry."""
        while True:
            try:
                print("Creating new pytchat session...")
                chat = pytchat.create(video_id=video_id)
                while chat.is_alive():
                    for c in chat.get().sync_items():
                        asyncio.create_task(self.process_message(c, timeout=5))
                    await asyncio.sleep(0.3)
                print("Chat session is no longer alive, restarting in 2 seconds...")
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Exception in chat_watcher: {e}. Restarting in 10 seconds...")
                await asyncio.sleep(10)

    async def periodic_status_report(self):
        while True:
            await asyncio.sleep(60)
            report = gen_status_report()
            await self.notify_clients(report)

    async def run(self):
        video_id = "hTwVzwT4Yno"
        server = await websockets.serve(self.handler, "0.0.0.0", 6789)

        asyncio.create_task(self.periodic_status_report())
        await asyncio.gather(
            self.chat_watcher(video_id),
            server.wait_closed(),
        )