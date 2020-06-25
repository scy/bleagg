# bleagg: BLE Aggregator

This is a small utility that queries my Xiaomi Mijia Bluetooth Low Energy (BLE) Temperature & Humidity Sensors that are deployed in [my van](https://github.com/scy/jessie) in regular intervals and sends the results to [IoTPlotter](https://iotplotter.com/).

## State

Works in production, but is somewhat unstable.
Also, currently you’ll have to install requirements manually.

Oh, and my sensors are hard-coded.
I’m sorry, this project is not perfectly polished, but I’m publishing it nevertheless, maybe somebody finds it useful.
Also, I have a backup on GitHub now.

“Unstable” means:
Either I’m using the [Bleak](https://github.com/hbldh/bleak) library wrong, or the Raspberry Pi the code is running on has problems with its Bluetooth stack.
Sometimes the queries will throw exceptions or even wait forever.
To mitigate this somewhat, I’ve chosen to simply ignore exceptions (missing a sensor once or twice isn’t a big deal) and add a `SIGALRM`-based watchdog to the script, i.e. it should exit after hanging for 30 seconds.

However, sometimes sensors can’t be queried for an extended amount of time, they always run into exceptions.
No idea what’s wrong there.
Also, I’ve had cases where the `SIGALRM` rang and the script still did not terminate, which is confusing.

## Running

I run it in a loop that will restart it on termination (see above for the `SIGALRM` mechanism).
You’ll have to provide your own IoTPlotter _Feed ID_ and _Key_.

```sh
while sleep 30; do sudo python3 bleagg.py -f 12345 -k 1a2b3c; done
```

## Contributing

If you’d like, I’m open for contributions.
Making it more stable and configurable would be my main priority.
Also, I want to change it to provide the sensor values for consumption by [Prometheus](https://prometheus.io/) soon™.
