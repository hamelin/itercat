from itercat import link


@link
async def increment(nums):
    async for num in nums:
        yield num + 1
