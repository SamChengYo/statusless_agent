import aiohttp
import asyncio

async def stream_upload():
    url = "http://localhost:8000/process-files"
    data = aiohttp.FormData()
    data.add_field('files', open('sample.pdf', 'rb'), filename='sample.pdf', content_type='application/pdf')
    data.add_field('files', open('sample3.pdf', 'rb'), filename='sample3.pdf', content_type='application/pdf')
    data.add_field('files', open('sample2.pdf', 'rb'), filename='sample2.pdf', content_type='application/pdf')
    data.add_field('mode', 's3')
    data.add_field('bucket_name', 'doc-ai-test-sam')

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data) as resp:
            print("Status:", resp.status)
            async for line in resp.content:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('data:'):
                    payload = decoded_line.removeprefix('data:').strip()
                    print(payload)

if __name__ == "__main__":
    asyncio.run(stream_upload())
