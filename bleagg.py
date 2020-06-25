import argparse
import asyncio
from bleak import BleakClient
import re
import signal
import sys
import time
from urllib import request

sensors = {
    "4C:65:A8:DC:06:78": "cockpit",
    "4C:65:A8:DC:29:07": "kitchen_upper_storage",
    "4C:65:A8:DC:1B:6A": "desk",
    "4C:65:A8:DC:1C:2C": "bathroom",
    "4C:65:A8:DC:30:A6": "bed",
}
uuid = "226caa55-6476-4566-7562-66734470666d"

class Sensor:
    def __init__(self, addr, name, loop):
        self.addr = addr
        self.name = name
        self.loop = loop
        self.waiting = False
        self.epoch = None
        self.temp = None
        self.hum = None

    def msg(self, *msg):
        print(self.name, *msg)

    async def query_once(self):
        self.msg("query_once")
        async with BleakClient(self.addr, loop=self.loop) as client:
            self.msg("connecting")
            await client.is_connected()
            self.waiting = True
            self.msg("starting notify")
            await client.start_notify(uuid, self.notification_handler)
            self.msg("notify running")
            waits = 0
            while waits < 10 and self.waiting:
                await asyncio.sleep(0.5, loop=loop)
                waits += 1
            self.msg("stopping notify")
            await client.stop_notify(uuid)
            self.msg("notify stopped")
            await asyncio.sleep(1.0, loop=loop)

    def notification_handler(self, sender, data):
        self.waiting = False
        match = re.match("T=(?P<T>[0-9.]+) H=(?P<H>[0-9.]+)\x00", data.decode("UTF-8"))
        if match:
            self.epoch = int(time.time())
            self.temp = float(match.group("T"))
            self.hum = float(match.group("H"))
        self.msg(self.temp, self.hum)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--feed-id", "-f", type=str, required=True)
    parser.add_argument("--key", "-k", type=str, required=True)
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    sensors = [Sensor(addr, name, loop) for (addr, name) in sensors.items()]

    # Exit on SIGALARM. This is our watchdog against hanging.
    signal.signal(signal.SIGALRM, lambda sig, stk: sys.exit(2))

    while True:
        for sensor in sensors:
            # Give each sonsor 30s do complete, or quit.
            signal.alarm(30)
            try:
                loop.run_until_complete(sensor.query_once())
            except:
                print(sensor.name, "oopsed")
        
        lines = []
        for sensor in sensors:
            if sensor.temp:
                lines.append("{0},{1}_{2},{3}".format(sensor.epoch, sensor.name, "temperature_c", sensor.temp))
            if sensor.hum:
                lines.append("{0},{1}_{2},{3}".format(sensor.epoch, sensor.name, "humidity_percent", sensor.hum))
        lines = "\n".join(lines)
        req = request.Request(
            "https://iotplotter.com/api/v2/feed/{0}.csv".format(args.feed_id),
            data=lines.encode(),
            headers={"api-key": args.key}
        )
        print(lines)
        request.urlopen(req).read()
        signal.alarm(60)
        time.sleep(30)
