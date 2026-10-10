"""Local Bilibili -> browser bridge. Credentials remain in process memory."""
import argparse
import asyncio
import getpass
import http.cookies
import json
from pathlib import Path
from aiohttp import web, ClientSession, ClientTimeout
import blivedm

ROOT = Path(__file__).resolve().parent.parent / 'web'

async def main(room, sessdata, port):
    clients = set()
    status = '离线桥接：未配置 B 站房间'
    async def broadcast(event):
        for ws in list(clients):
            try:
                await ws.send_json(event)
            except (ConnectionError, RuntimeError):
                clients.discard(ws)
    def emit(event):
        asyncio.create_task(broadcast(event))
    def change(text):
        nonlocal status
        status = text
        emit({'type': 'status', 'text': text})
    class Handler(blivedm.BaseHandler):
        def _on_gift(self, client, m):
            emit({'type': 'gift', 'source': 'bilibili', 'uid': str(m.uid),
                  'name': m.uname, 'avatar': m.face, 'giftId': m.gift_id,
                  'giftName': m.gift_name, 'giftIcon': m.gift_img_basic,
                  'quantity': m.num, 'transactionId': str(m.tid or m.rnd or '')})
        def _on_danmaku(self, client, m):
            emit({'type': 'danmaku', 'uid': str(m.uid), 'name': m.uname,
                  'avatar': m.face, 'text': m.msg})
        def on_client_stopped(self, client, exception):
            change('B 站监听停止，请重启桥接' if exception else 'B 站监听已停止')
    class Client(blivedm.BLiveClient):
        async def _on_ws_connect(self):
            await super()._on_ws_connect()
            change(f'B 站已连接 · 房间 {room}')
        async def _on_ws_close(self):
            await super()._on_ws_close()
            change('B 站连接中断，正在重连')
    async def events(request):
        # Only same-origin browser pages may use this local service.
        origin = request.headers.get('Origin')
        if origin and origin != f'http://127.0.0.1:{port}':
            raise web.HTTPForbidden(text='Open the game from the local bridge URL')
        ws = web.WebSocketResponse(heartbeat=20)
        await ws.prepare(request)
        clients.add(ws)
        await ws.send_json({'type': 'status', 'text': status})
        try:
            async for _ in ws:
                pass
        finally:
            clients.discard(ws)
        return ws
    session = ClientSession(timeout=ClientTimeout(total=15))
    if sessdata:
        cookie = http.cookies.SimpleCookie()
        if 'SESSDATA=' in sessdata:
            cookie.load(sessdata)
            sessdata = cookie['SESSDATA'].value if 'SESSDATA' in cookie else ''
        cookie = http.cookies.SimpleCookie()
        cookie['SESSDATA'] = sessdata
        cookie['SESSDATA']['domain'] = 'bilibili.com'
        session.cookie_jar.update_cookies(cookie)
    async def catalog(request):
        if not room:
            raise web.HTTPBadRequest(text='No room configured')
        url = 'https://api.live.bilibili.com/xlive/web-room/v1/giftPanel/roomGiftList'
        try:
            async with session.get(url, params={'platform': 'pc', 'room_id': room}, headers={'Referer': f'https://live.bilibili.com/{room}', 'User-Agent': 'Mozilla/5.0'}) as resp:
                payload = await resp.json()
            if payload.get('code') != 0:
                raise ValueError('Bilibili rejected catalog request')
            cfg = payload.get('data', {}).get('gift_config', {})
            entries = cfg.get('base_config', {}).get('list', []) + cfg.get('room_config', [])
            gifts = {int(g['id']): {'id': g['id'], 'name': g.get('name', ''), 'icon': g.get('img_basic', '')} for g in entries if isinstance(g, dict) and g.get('id')}
            return web.json_response(list(gifts.values()))
        except Exception:
            raise web.HTTPBadGateway(text='Gift catalog unavailable; check room and network')
    app = web.Application()
    app.router.add_get('/events', events)
    app.router.add_get('/catalog', catalog)
    app.router.add_get('/', lambda request: web.FileResponse(ROOT / 'index.html'))
    app.router.add_static('/', ROOT)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '127.0.0.1', port).start()
    print(f'打开 http://127.0.0.1:{port}；Ctrl+C 停止。')
    client = None
    try:
        if room:
            change(f'正在连接 B 站房间 {room}')
            client = Client(room, session=session)
            client.set_handler(Handler())
            client.set_reconnect_policy(lambda retries, total: min(30, 1.5 * 2 ** min(max(0, retries-1), 4)))
            client.start()
        await asyncio.Event().wait()
    finally:
        if client:
            await client.stop_and_close()
        await runner.cleanup()
        await session.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--room', type=int, default=0)
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--login', action='store_true')
    args = parser.parse_args()
    secret = getpass.getpass('SESSDATA（隐藏输入，仅本次进程使用）: ') if args.login else ''
    try:
        asyncio.run(main(args.room, secret, args.port))
    except KeyboardInterrupt:
        pass
