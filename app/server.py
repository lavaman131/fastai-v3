import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

export_file_url = 'https://www.googleapis.com/drive/v3/files/1WhOHeTq6xCSSYjtBcaegW4ncBIIklgp4?alt=media&key=AIzaSyA1_i8JANU6zKYqBYUaI3dcgvTTgQJFkkw'
export_file_name = 'FINAL_LEAF_MODEL3.pkl'

classes = ['Apple Black rot',
 'Apple Healthy',
 'Apple Scab',
 'Bell pepper Bacterial spot',
 'Bell pepper Healthy',
 'Cedar apple rust',
 'Cherry Healthy',
 'Cherry Powdery mildew',
 'Citrus Black spot',
 'Citrus Healthy',
 'Citrus canker',
 'Citrus greening',
 'Corn Common rust',
 'Corn Gray leaf spot',
 'Corn Healthy',
 'Corn Northern Leaf Blight',
 'Grape Black Measles',
 'Grape Black rot',
 'Grape Healthy',
 'Grape Isariopsis Leaf Spot',
 'Peach Bacterial spot',
 'Peach Healthy',
 'Potato Early blight',
 'Potato Healthy',
 'Potato Late blight',
 'Strawberry Healthy',
 'Strawberry Leaf scorch',
 'Tomato Bacterial spot',
 'Tomato Early blight',
 'Tomato Healthy',
 'Tomato Late blight',
 'Tomato Leaf Mold',
 'Tomato Mosaic virus',
 'Tomato Septoria leaf spot',
 'Tomato Spider mites',
 'Tomato Target Spot',
 'Tomato Yellow Leaf Curl Virus']

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    final_img = img.resize(torch.Size([img.shape[0],224, 224]))
    prediction = learn.predict(final_img)[0]
    return JSONResponse({'result': str(prediction)})
   
   
if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
