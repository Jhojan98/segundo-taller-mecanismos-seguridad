#!/usr/bin/env python3
"""Sesión XMPP mínima para el laboratorio (envío y recepción de un mensaje).

Uso:
  python3 xmpp_session.py --role receiver --jid bob@lab.local --password bob123 \
      --server 172.28.50.30 --port 5222 --insecure --wait 12
  python3 xmpp_session.py --role sender --jid alice@lab.local --password alice123 \
      --recipient bob@lab.local --message "HOLA-BOB-..." \
      --server 172.28.50.30 --port 5222 --insecure
"""
import argparse
import asyncio
import ssl
import sys

import slixmpp


class LabClient(slixmpp.ClientXMPP):
    def __init__(self, args):
        plugin_config = {
            "feature_mechanisms": {"unencrypted_plain": bool(args.no_starttls)}
        }
        super().__init__(args.jid, args.password, plugin_config=plugin_config,
                         sasl_mech=args.sasl or None)
        self.args = args

        if args.insecure:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self.ssl_context = ctx
        elif args.ca:
            self.ssl_context = ssl.create_default_context(cafile=args.ca)

        self.add_event_handler("session_start", self.session_start)
        self.add_event_handler("message", self.on_message)

    async def session_start(self, event):
        self.send_presence()
        await self.get_roster()
        if self.args.role == "sender":
            self.send_message(mto=self.args.recipient, mbody=self.args.message, mtype="chat")
            print("SENT", flush=True)
            await asyncio.sleep(1.5)
            self.disconnect()
        else:
            print("RECEIVER_READY", flush=True)
            await asyncio.sleep(self.args.wait)
            self.disconnect()

    def on_message(self, msg):
        if msg["type"] in ("chat", "normal") and msg["body"]:
            print("RECEIVED:" + msg["body"], flush=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--role", choices=["sender", "receiver"], required=True)
    p.add_argument("--jid", required=True)
    p.add_argument("--password", required=True)
    p.add_argument("--recipient", default="")
    p.add_argument("--message", default="")
    p.add_argument("--server", required=True)
    p.add_argument("--port", type=int, default=5222)
    p.add_argument("--insecure", action="store_true")
    p.add_argument("--no-starttls", action="store_true")
    p.add_argument("--sasl", default="")
    p.add_argument("--ca", default="")
    p.add_argument("--wait", type=int, default=10)
    args = p.parse_args()

    client = LabClient(args)
    client.connect(address=(args.server, args.port), disable_starttls=args.no_starttls)
    client.process(forever=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
