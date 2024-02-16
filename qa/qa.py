from aiohttp import web


def get_answer_gigachat(question: str) -> str:
    pass


@routes.post('/qa/')
async def qa(request):
    question = (await request.json())['question']
    return web.Response(text=get_answer_gigachat(question))


@routes.post('/reindex/')
async def reindex(request):
    return web.Response(200)


if __name__ == "__main__":
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app)
