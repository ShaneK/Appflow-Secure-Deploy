from machine import Pin
import uasyncio
import urequests
import services.appflow

from env.env import Environment
from services.wifi import *

led = Pin("LED", Pin.OUT)
big_red_button = Pin(15, Pin.IN, Pin.PULL_UP)
big_red_button.value(0)


async def main():
    connection_status = ConnectionStatus.NOT_CONNECTED
    big_red_button_in_progress = False
    ready_to_deploy = False

    async def monitor_connection_status(station):
        nonlocal connection_status
        while True:
            if station.isconnected():
                connection_status = ConnectionStatus.CONNECTED
            else:
                connection_status = ConnectionStatus.NOT_CONNECTED
            await uasyncio.sleep_ms(500)

    def load_destinations():
        print("Loading destinations...")
        services.appflow.get_channels()
        print("Loaded destinations!")


    async def check_ready_to_deploy():
        nonlocal ready_to_deploy
        while not ready_to_deploy:
            # Load critical data
            # Builds
            builds = await services.appflow.get_builds()
            print(f"Builds: {builds}")
            # We've just made a big request, let something else go
            await uasyncio.sleep_ms(50)
            # Destinations
            destinations = await services.appflow.get_channels()
            print(f"Destinations: {destinations}")
            # We've just made a big request, let something else go
            ready_to_deploy = True
            await uasyncio.sleep_ms(50)

    async def setup_wifi():
        try:
            nonlocal connection_status
            connection_status = ConnectionStatus.CONNECTING
            print(f"Searching for {Environment.SSID}...")
            station = await connect_wifi(Environment.SSID, Environment.SSID_PASSWORD)
            intra_ipaddress, _, _, _ = station.ifconfig()
            uasyncio.create_task(monitor_connection_status(station))
            response = (urequests.get("http://httpbin.org/ip")).json()
            print("----\nIP Info:\n----")
            print(f"Internal IP Address: {intra_ipaddress}")
            print(f"External IP Address: {response['origin']}")
            uasyncio.create_task(check_ready_to_deploy())
        except Exception as e:
            print(e)

    async def display_connection_status():
        while True:
            led.value(big_red_button.value())
            if connection_status == ConnectionStatus.CONNECTED:
                led.value(1)
            elif connection_status == ConnectionStatus.CONNECTING:
                led.value(1)
                await uasyncio.sleep_ms(500)
                led.value(0)
            else:
                led.value(0)
            await uasyncio.sleep_ms(500)

    async def monitor_big_red_button():
        while True:
            nonlocal big_red_button_in_progress
            # if big_red_button.value() == 1:
            if False:
                if big_red_button_in_progress:
                    await uasyncio.sleep_ms(50)
                    continue

                big_red_button_in_progress = True
                print("Button pressed! Fetching builds...")
                big_red_button_in_progress = False

            # For when the big read button isn't down
            await uasyncio.sleep_ms(50)

    uasyncio.create_task(display_connection_status())
    uasyncio.create_task(setup_wifi())
    uasyncio.create_task(monitor_big_red_button())
    print("Welcome!")

    while True:
        # Effectively doing nothing, but keeping the program alive to asynchronously do everything else
        # This is kind of dumb, but effectively by doing this we're allowing our tasks to be grouped and
        # named instead of just living here, un-named and un-grouped.
        await uasyncio.sleep_ms(1000)


uasyncio.run(main())
