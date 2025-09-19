import asyncio
import json

from game import Game
from models.user import block_user
from web_socket import gen_status_report


class CLIClient:
    def __init__(self, game: Game):
        self.game = game
        self.clients = set()

    async def run(self):
        while True:
            cmd_txt = await asyncio.to_thread(input, ">>> ")  # run input() in a background thread
            if not cmd_txt:
                continue
            elif len(cmd_txt.strip().split()) == 1:
                cmd = cmd_txt
                param = ''
            else:
                cmd, param = cmd_txt.strip().split(maxsplit=1)
            cmd = cmd.lower()

            if cmd == 'status':
                print(json.dumps(gen_status_report(), indent=2))
            elif cmd == 'block':
                success = block_user(user_name=param)
                if not success:
                    print('Unsuccessful block, or faulty request.')
            elif cmd == 'unblock':
                success = block_user(user_name=param, block_duration_seconds=False)
                if not success:
                    print('Unsuccessful at reverting user block, or faulty request.')
            elif cmd == 'quit':
                print("Shutting down...")
                for client in list(self.clients):
                    await client.close()
                asyncio.get_event_loop().stop()
                break
            else:
                print(f"Unknown command: {cmd}")
