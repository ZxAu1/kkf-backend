from asyncua import Client
import asyncio
import os
async def opc():
    async with Client(url='opc.tcp://191.20.80.102:49320') as client:
        while True:
            # Do something with client
            dist_x = await client.get_node('ns=2;s=LINE05-MP.ASRS.Distance_X').read_value()
            dist_y = await client.get_node('ns=2;s=LINE05-MP.ASRS.Distance_Y').read_value()
            print((dist_x, dist_y))
            await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.run_until_complete(opc())