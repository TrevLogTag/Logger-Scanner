import asyncio
from bleak import *
from bleak.backends.scanner import AdvertisementData
from aioconsole import ainput
from datetime import datetime

devices = ["FE:A9:04:78:B6:C9", "CA:84:BC:CC:11:21"]
TEMPERATURE_UUID = "00002a1c-0000-1000-8000-00805f9b34fb"
HUMIDITY_UUID = "00002a6f-0000-1000-8000-00805f9b34fb"
BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
UART_RX_UUID = (
    "6e400003-b5a3-f393-e0a9-e50e24dcca9e"  # Nordic NUS characteristic for RX
)
UART_TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"


class Connection:
    isConnect = False
    chosen_index = None

    def __init__(self, loop: asyncio.AbstractEventLoop, read_characteristic: str):
        self.read_characteristic = read_characteristic
        self.last_packet_time = datetime.now()
        self.connected = False
        self.loop = loop

        self.rx_data = []
        self.rx_timestamps = []
        self.rx_delays = []
        self.temp_data = []

    async def manager(self):
        print("STARTING CONNECTION MANAGER")
        while True:
            if self.isConnect:
                await self.connect()
            else:
                await self.select_device()

    async def connect(self):
        isConnectFlag = False
        while isConnectFlag == False:
            print("Connecting to " + devices[int(self.chosen_index)])
            client = BleakClient(devices[int(self.chosen_index)])
            try:
                await client.connect()
                print("Connection Successful")

                while 1:
                    await notification_manager(client)
                    # svcs = await client.get_services()
                    # for service in svcs:
                    #    print(service)
                isConnect = True
            except Exception as e:
                print(e)
            finally:
                await client.disconnect()
            await asyncio.sleep(2.0)

    async def select_device(self):
        print("Select device to connect")
        print("0: Name: LOG-IC 360 | Address: FE:A9:04:78:B6:C9")
        print("1: Name: TZ-BT04 | Address: CA:84:BC:CC:11:21")

        # Get input
        while 1:
            response = await ainput()
            if response == "0":
                self.isConnect = True
                self.chosen_index = response
                break
            elif response == "1":
                self.isConnect = True
                self.chosen_index = response
                break
            else:
                print("Invalid Input")

    def record_time_info(self):
        present_time = datetime.now()
        self.rx_timestamps.append(present_time)
        self.rx_delays.append((present_time - self.last_packet_time).microseconds)
        self.last_packet_time = present_time

    def clear_lists(self):
        self.rx_data.clear()
        self.rx_delays.clear()
        self.rx_timestamps.clear()


async def main():
    isConnect = False
    while isConnect == False:
        print("Connecting to " + devices[0])
        client = BleakClient(devices[0])
        try:
            await client.connect()
            BleakScanner.advertisement_data
            while 1:
                await notification_manager(client)

            isConnect = True
        except Exception as e:
            print(e)
        finally:
            await client.disconnect()
        await asyncio.sleep(2.0)


async def notification_manager(client):
    print("Waiting...")
    await client.start_notify(TEMPERATURE_UUID, temp_notification_handler)
    await client.start_notify(HUMIDITY_UUID, humidity_notification_handler)
    await asyncio.sleep(2.0)
    await client.stop_notify(TEMPERATURE_UUID)
    await client.stop_notify(HUMIDITY_UUID)


def notification_handler(sender, data):
    print("{0}: {1}".format(sender, data))


def temp_notification_handler(sender, data):
    current_temperature = int.from_bytes(data, byteorder="little", signed=True) / 100
    print("Temperature: {0} Celsius".format(current_temperature))


def humidity_notification_handler(sender, data):
    current_humidity = int.from_bytes(data, byteorder="little", signed=False) / 100
    print("Humidity: {0} %".format(current_humidity))


if __name__ == "__main__":
    # Create the event loop.
    loop = asyncio.get_event_loop()

    connection = Connection(loop, UART_RX_UUID)
    try:
        asyncio.ensure_future(connection.manager())
        loop.run_forever()
        # asyncio.run(main())
    except KeyboardInterrupt:
        # CTRL + C
        print()
        print("User stopped program")
    finally:
        print("Disconnecting")
