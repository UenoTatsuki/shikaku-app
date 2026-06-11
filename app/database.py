"""データベースの接続まわりをまとめたファイル。

SQLite を使う。アプリのフォルダに shikaku.db というファイルが作られ、
そこにデータが保存される（サーバーを止めても消えない）。
"""

from sqlmodel import SQLModel, create_engine, Session

# データベースの場所。"sqlite:///./shikaku.db" は
# 「このフォルダの shikaku.db というファイルを使う」という意味。
DATABASE_URL = "sqlite:///./shikaku.db"

# engine は DB への“接続口”。echo=True にすると、裏で実行される
# SQL がターミナルに表示され、学習中は何が起きているか分かりやすい。
# check_same_thread=False は SQLite を FastAPI で使うときのお約束。
engine = create_engine(
    DATABASE_URL,
    echo=True,
    connect_args={"check_same_thread": False},
)


def init_db() -> None:
    """models.py で定義したテーブルを（なければ）作る。"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """API が DB を触るときに使うセッションを 1 つ渡す。

    FastAPI の Depends と組み合わせて使う。処理が終わると自動で閉じる。
    """
    with Session(engine) as session:
        yield session
