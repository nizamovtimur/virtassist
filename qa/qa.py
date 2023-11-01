from aiohttp import web

routes = web.RouteTableDef()


@routes.post('/')
async def main(request):
    question = (await request.json())['question']
    return web.Response(text=f"Hello! Your question is {question}")


app = web.Application()
app.add_routes(routes)
web.run_app(app)
