import asyncio, subprocess, sys
from aiohttp import ClientSession
async def test():
    process = subprocess.Popen([sys.executable, 'bridge/server.py', '--port', '8766'], stdout=subprocess.DEVNULL)
    try:
        async with ClientSession() as session:
            for _ in range(50):
                try:
                    async with session.get('http://127.0.0.1:8766/') as response:
                        assert response.status == 200
                        assert '主播拌面店' in await response.text()
                    break
                except OSError:
                    await asyncio.sleep(.1)
            else:
                raise AssertionError('Bridge did not start')
            async with session.ws_connect('http://127.0.0.1:8766/events', origin='http://127.0.0.1:8766') as ws:
                data = await ws.receive_json(timeout=2)
                assert data['type'] == 'status' and '离线' in data['text']
        print('PASS: bridge startup, HTML serving, WebSocket status')
    finally:
        process.terminate()
        process.wait(timeout=5)
asyncio.run(test())
