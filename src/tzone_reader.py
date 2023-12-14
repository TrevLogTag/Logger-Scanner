import asyncio
from bleak import *
from datetime import timedelta
import datetime
from aioconsole import ainput

LOGIC_360 = "FE:A9:04:78:B6:C9"
TZ_BT04 = "CA:84:BC:CC:11:21"

password_UUID = "27763B13-999C-4D6A-9FC4-c7272BE10900"
data_mode_UUID = "27763B31-999C-4D6A-9FC4-C7272BE10900"
sync_dataswitch_UUID = "27763B21-999C-4D6A-9FC4-C7272BE10900"  # To read past data
degree_sign = "\N{DEGREE SIGN}"


async def main():
    print("TZONE READER")
    print("0: Broadcasted Data")
    print("1: Stored Data")
    print("2: Output services")

    # Get input
    while 1:
        response = await ainput()
        if response == "0":
            await get_broadcast_data()
            break
        elif response == "1":
            await get_stored_data()
            break
        elif response == "2":
            await print_services()
            break
        else:
            print("Invalid Input")


# Get stored data function
async def get_stored_data():
    print("STORED DATA =>")
    isConnect = False
    while isConnect == False:
        print("Connecting to " + TZ_BT04)
        client = BleakClient(TZ_BT04, timeout=15.0)
        try:
            await client.connect()
            print("Connection Successful")
            await get_data(client)

            isConnect = True
        except Exception as e:
            print(e)
        finally:
            await client.disconnect()
        


# Get broadcasted data function
async def get_broadcast_data():
    print("BROADCASTED DATA =>")
    scanner = BleakScanner(detection_callback)
    print("Starting scanner...")
    while True:
        await scanner.start()
        await asyncio.sleep(30.0)
        await scanner.stop()
        print("(Re)starting scanner")


# Print services
async def print_services():
    isConnect = False
    while isConnect == False:
        print("Connecting to " + TZ_BT04)
        client = BleakClient(TZ_BT04, timeout=15.0)
        try:
            await client.connect()
            print("Connection Successful")
            services = await client.get_services()
            for svcs in services:
                print(svcs)

            isConnect = True
        except Exception as e:
            print(e)
        finally:
            await client.disconnect()


# Handles advertising packets scanned
def detection_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    if device.address == TZ_BT04:
        dict = advertisement_data.service_data
        data = dict["0000cbff-0000-1000-8000-00805f9b34fb"].hex()
        device_id = data[8:16]
        battery = int(data[16:18], 16)
        temp = int(data[20:24], 16)
        parsed_temp = round((float(temp) * 0.01), 1)
        humidity = int(data[24:28], 16)
        parsed_humidity = round((float(humidity) * 0.01), 1)
        print(
            "DEVICE ID: "
            + device_id
            + " | BATTERY: "
            + str(battery)
            + "% | TEMP: "
            + str(parsed_temp)
            + degree_sign
            + "C | HUMIDITY: "
            + str(parsed_humidity)
            + "%"
        )


# This function is called everytime a packet is sent
def notification_handler(sender, data):
    # print("{0}: {1}".format(sender, data.hex()))
    # print(data.hex())
    byte_parser(data)


def byte_parser(data: bytearray):
    data_hex = bytes(data).hex()
    first_reading = data_hex[0:14]
    second_reading = data_hex[14:28]

    # Parse readings
    reader(first_reading)
    reader(second_reading)


def reader(reading: str):
    date = reading[0:8]
    values = reading[8:14]

    # Convert to datetime format
    dtime_obj = datetime.datetime.fromtimestamp(int(date, 16))
    dtime_obj += timedelta(hours=12)
    datetime_str = dtime_obj.strftime("%Y-%m-%d %H:%M:%S")

    # Get temperature and humidity
    if values:
        # Calculate temp
        temp_binary = (int(values, 16) >> 6) & 0x007FF
        temp = int(temp_binary)
        temp = float(temp) * 0.1
        temp = round(temp, 1)

        # Calculate humidity
        humidity_hex = values[0:2]
        humidity_binary = (int(humidity_hex, 16)) >> 1
        humidity = int(humidity_binary)

        print(
            datetime_str
            + " | TEMP: "
            + str(temp)
            + degree_sign
            + "C | HUMIDITY: "
            + str(humidity)
            + "%"
        )


async def get_data(client):
    print("Send password...")
    bytes_to_send = bytearray([0x00, 00, 00, 00, 00, 00])
    print("SENT: 0x00, 00, 00, 00, 00, 00")
    await client.write_gatt_char(password_UUID, bytes_to_send)

    print()
    print("Getting data...")
    await client.start_notify(sync_dataswitch_UUID, notification_handler)
    await asyncio.sleep(10.0)
    await client.stop_notify(sync_dataswitch_UUID)


asyncio.run(main())
