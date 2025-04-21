import asyncio

from gi.events import GLibEventLoopPolicy

# Set up the GLib event loop
policy = GLibEventLoopPolicy()
asyncio.set_event_loop_policy(policy)
loop = policy.get_event_loop()


async def do_some_work():
    await asyncio.sleep(2)
    print("Done working! (1)")


async def do_some_work_2():
    for i in range(10):
        print(f"Working...(2) ({i})")
        await asyncio.sleep(1)
    await asyncio.sleep(1)
    print("Done working! (2)")


task = loop.create_task(do_some_work())
task_2 = loop.create_task(do_some_work_2())
print("Task created, waiting for it to finish...")
loop.run_until_complete(task_2)
print("Task finished!")
loop.close()
