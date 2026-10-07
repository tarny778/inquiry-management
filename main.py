from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

app = FastAPI()



@app.get("/", response_class=HTMLResponse)
def inquiry_form():
    return """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>問い合わせ登録</title>
    </head>
    <body>
        <h1>問い合わせ登録</h1>

        <form action="/inquiries" method="post">
            <p>
                件名<br>
                <input type="text" name="title">
            </p>

            <p>
                会社名<br>
                <input type="text" name="company">
            </p>

            <p>
                内容<br>
                <textarea name="content"></textarea>
            </p>

            <button type="submit">登録する</button>
        </form>
    </body>
    </html>
    """


@app.post("/inquiries", response_class=HTMLResponse)
def create_inquiry(
    title: str = Form(...),
    company: str = Form(...),
    content: str = Form(...),
):
    return f"""
    <h1>問い合わせを登録しました</h1>

    <p><strong>件名：</strong>{title}</p>
    <p><strong>会社名：</strong>{company}</p>
    <p><strong>内容：</strong>{content}</p>

    <a href="/">戻る</a>
    """