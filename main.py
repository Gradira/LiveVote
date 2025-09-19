import asyncio

from cli import CLIClient
from game import Game
from web_socket import WebsocketClient

if __name__ == "__main__":
    with Game() as game:
        ws_client = WebsocketClient(game)  # Websocket for webpages
        cli_client = CLIClient(game)  # command line interface
        asyncio.run(ws_client.run())

        # asyncio.run(cli_client.run())
        asyncio.create_task(cli_client.run())
