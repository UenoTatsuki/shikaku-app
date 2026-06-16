"""FastAPI 本体。

今はスライス 1（資格の登録・一覧・詳細・更新・削除＋試験日カウントダウン）
だけを実装している。スライス 2 以降は、この下に同じ書き方で
エンドポイントを足していく（末尾の TODO メモ参照）。

起動方法は README.md を参照。起動後 http://127.0.0.1:8000/docs を開くと、
ブラウザ上で全 API を試せる（FastAPI が自動で用意してくれる画面）。
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel, select

from .database import init_db, get_session
from .models import Certification, StudySession, Textbook, Flashcard, Todo

app = FastAPI(title="資格学習アプリ API")


@app.on_event("startup")
def on_startup() -> None:
    """サーバー起動時にテーブルを用意する。"""
    init_db()


# ---- 入力・出力の形（スキーマ）------------------------------------------

class CertificationCreate(SQLModel):
    """資格を登録・更新するときに受け取るデータの形。"""
    name: str
    exam_date: Optional[date] = None
    status: str = "studying"


class CertificationRead(SQLModel):
    """資格を返すときの形。残り日数（カウントダウン）を加える。"""
    id: int
    name: str
    exam_date: Optional[date]
    status: str
    days_until_exam: Optional[int]   # 試験日までの残り日数。試験日が空なら None


def to_read(cert: Certification) -> CertificationRead:
    """DB のデータに「残り日数」を計算して足し、返す形に変換する。"""
    days = None
    if cert.exam_date is not None:
        days = (cert.exam_date - date.today()).days
    return CertificationRead(
        id=cert.id,
        name=cert.name,
        exam_date=cert.exam_date,
        status=cert.status,
        days_until_exam=days,
    )


# ---- 資格の API（スライス 1）--------------------------------------------

@app.post("/certifications", response_model=CertificationRead)
def create_certification(
    data: CertificationCreate,
    session: Session = Depends(get_session),
):
    """資格を 1 件登録する。"""
    cert = Certification(**data.model_dump())
    session.add(cert)
    session.commit()
    session.refresh(cert)   # 採番された id を反映
    return to_read(cert)


@app.get("/certifications", response_model=List[CertificationRead])
def list_certifications(session: Session = Depends(get_session)):
    """資格を一覧で返す（各件に残り日数つき）。"""
    certs = session.exec(select(Certification)).all()
    return [to_read(c) for c in certs]


@app.get("/certifications/{cert_id}", response_model=CertificationRead)
def get_certification(cert_id: int, session: Session = Depends(get_session)):
    """資格 1 件の詳細を返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    return to_read(cert)


@app.patch("/certifications/{cert_id}", response_model=CertificationRead)
def update_certification(
    cert_id: int,
    data: CertificationCreate,
    session: Session = Depends(get_session),
):
    """資格を更新する。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    cert.name = data.name
    cert.exam_date = data.exam_date
    cert.status = data.status
    session.add(cert)
    session.commit()
    session.refresh(cert)
    return to_read(cert)


@app.delete("/certifications/{cert_id}")
def delete_certification(cert_id: int, session: Session = Depends(get_session)):
    """資格を削除する。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    session.delete(cert)
    session.commit()
    return {"ok": True}

# ---- 学習記録の API (スライス 2)-------------------------------------------

class StudySessionCreate(SQLModel):
    """勉強を一回記録するときに受け取るデータ"""
    duration_min: int                    #勉強した時間 (分)
    studied_at: Optional[date] = None    #学習日。省略したら今日になる


@app.post("/certifications/{cert_id}/sessions")
def create_session(
    cert_id: int,
    data: StudySessionCreate,
    session: Session = Depends(get_session),
):
    """指定した資格に、勉強記録を１件保存する"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    record = StudySession(
        certification_id=cert_id,
        duration_min=data.duration_min,
        studied_at=data.studied_at or date.today(),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


@app.get("/certifications/{cert_id}/sessions")
def list_sessions(cert_id: int, session: Session = Depends(get_session)):
    """その資格の勉強記録の一覧と、総勉強時間（分）を返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    records = session.exec(
        select(StudySession).where(StudySession.certification_id == cert_id)
    ).all()
    total = sum(r.duration_min for r in records)
    return {"total_min": total, "sessions": records}


# ---- 参考書の API（スライス 3）------------------------------------------

class TextbookCreate(SQLModel):
    """参考書を登録するときに受け取るデータ。"""
    title: str
    current_chapter: int = 0           # 今いる章（最初は0）
    total_chapters: Optional[int] = None  # 全章数（任意）


class TextbookUpdate(SQLModel):
    """進捗などを更新するときのデータ。送った項目だけが変わる。"""
    title: Optional[str] = None
    current_chapter: Optional[int] = None
    total_chapters: Optional[int] = None


@app.post("/certifications/{cert_id}/textbooks")
def create_textbook(
    cert_id: int,
    data: TextbookCreate,
    session: Session = Depends(get_session),
):
    """指定した資格に参考書を1冊登録する。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    book = Textbook(certification_id=cert_id, **data.model_dump())
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@app.get("/certifications/{cert_id}/textbooks")
def list_textbooks(cert_id: int, session: Session = Depends(get_session)):
    """その資格の参考書一覧を返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    books = session.exec(
        select(Textbook).where(Textbook.certification_id == cert_id)
    ).all()
    return books


@app.patch("/textbooks/{textbook_id}")
def update_textbook(
    textbook_id: int,
    data: TextbookUpdate,
    session: Session = Depends(get_session),
):
    """参考書の進捗（現在の章など）を更新する。送った項目だけ変わる。"""
    book = session.get(Textbook, textbook_id)
    if book is None:
        raise HTTPException(status_code=404, detail="参考書が見つかりません")
    update_data = data.model_dump(exclude_unset=True)  # 送られた項目だけ取り出す
    for key, value in update_data.items():
        setattr(book, key, value)
    session.add(book)
    session.commit()
    session.refresh(book)
    return book


@app.delete("/textbooks/{textbook_id}")
def delete_textbook(textbook_id: int, session: Session = Depends(get_session)):
    """参考書を削除する。"""
    book = session.get(Textbook, textbook_id)
    if book is None:
        raise HTTPException(status_code=404, detail="参考書が見つかりません")
    session.delete(book)
    session.commit()
    return {"ok": True}


# ---- 暗記カードの API（スライス 4）------------------------------------------

# 箱番号ごとの「次の出題までの日数」。箱が上がるほど間隔が延びる。
BOX_INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30}


class FlashcardCreate(SQLModel):
    """カードを登録するときのデータ。"""
    question: str   # 問題（表）
    answer: str     # 答え（裏）


class ReviewResult(SQLModel):
    """復習の結果。正解なら true、不正解なら false。"""
    correct: bool


@app.post("/certifications/{cert_id}/cards")
def create_card(
    cert_id: int,
    data: FlashcardCreate,
    session: Session = Depends(get_session),
):
    """指定した資格にカードを1枚登録する。作った直後から復習対象になる。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    card = Flashcard(
        certification_id=cert_id,
        question=data.question,
        answer=data.answer,
        box=1,
        next_due=date.today(),   # 今日から出題対象
    )
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


@app.get("/certifications/{cert_id}/cards")
def list_cards(cert_id: int, session: Session = Depends(get_session)):
    """その資格のカードを全部返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    cards = session.exec(
        select(Flashcard).where(Flashcard.certification_id == cert_id)
    ).all()
    return cards


@app.get("/certifications/{cert_id}/cards/due")
def list_due_cards(cert_id: int, session: Session = Depends(get_session)):
    """今日復習すべきカード（next_due が今日以前）だけを返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    today = date.today()
    cards = session.exec(
        select(Flashcard).where(
            Flashcard.certification_id == cert_id,
            Flashcard.next_due <= today,
        )
    ).all()
    return cards


@app.post("/cards/{card_id}/review")
def review_card(
    card_id: int,
    data: ReviewResult,
    session: Session = Depends(get_session),
):
    """復習結果を受け取り、箱と次回出題日を更新する（このアプリの核）。"""
    card = session.get(Flashcard, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="カードが見つかりません")
    if data.correct:
        card.box = min(card.box + 1, 5)   # 正解：1つ上の箱へ（最大5）
    else:
        card.box = 1                      # 不正解：箱1に戻す
    interval = BOX_INTERVALS[card.box]
    card.next_due = date.today() + timedelta(days=interval)
    session.add(card)
    session.commit()
    session.refresh(card)
    return card


# ---- Todo の API（スライス 5）------------------------------------------

class TodoCreate(SQLModel):
    """タスクを追加するときのデータ。"""
    title: str


class TodoUpdate(SQLModel):
    """タスクの更新。完了切り替えや内容変更に使う。送った項目だけ変わる。"""
    title: Optional[str] = None
    is_done: Optional[bool] = None


@app.post("/certifications/{cert_id}/todos")
def create_todo(
    cert_id: int,
    data: TodoCreate,
    session: Session = Depends(get_session),
):
    """指定した資格にタスクを1件追加する。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    todo = Todo(certification_id=cert_id, title=data.title)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.get("/certifications/{cert_id}/todos")
def list_todos(cert_id: int, session: Session = Depends(get_session)):
    """その資格のタスク一覧を返す。"""
    cert = session.get(Certification, cert_id)
    if cert is None:
        raise HTTPException(status_code=404, detail="資格が見つかりません")
    todos = session.exec(
        select(Todo).where(Todo.certification_id == cert_id)
    ).all()
    return todos


@app.patch("/todos/{todo_id}")
def update_todo(
    todo_id: int,
    data: TodoUpdate,
    session: Session = Depends(get_session),
):
    """タスクを更新する（完了の切り替え・内容変更）。"""
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(todo, key, value)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


@app.delete("/todos/{todo_id}")
def delete_todo(todo_id: int, session: Session = Depends(get_session)):
    """タスクを削除する。"""
    todo = session.get(Todo, todo_id)
    if todo is None:
        raise HTTPException(status_code=404, detail="タスクが見つかりません")
    session.delete(todo)
    session.commit()
    return {"ok": True}


# =========================================================================
# ここから下は、これから作る部分のメモ（スライス 2 以降）。
# 同じパターンで、ファイル上部の import に必要なモデルを足しながら実装する。
#
# スライス 2: 学習タイマー（StudySession）
#   POST /certifications/{cert_id}/sessions   勉強記録を 1 件保存
#   GET  /certifications/{cert_id}/sessions   記録一覧＋合計時間（duration_min の合計）
#
# スライス 3: 参考書進捗（Textbook）
#   POST  /certifications/{cert_id}/textbooks  参考書を登録
#   GET   /certifications/{cert_id}/textbooks  参考書一覧
#   PATCH /textbooks/{textbook_id}             現在の章を更新
#   DELETE /textbooks/{textbook_id}            削除
#
# スライス 4: 暗記カード（Flashcard）※このアプリの核
#   POST /certifications/{cert_id}/cards       カード登録
#   GET  /certifications/{cert_id}/cards/due   今日復習すべきカード（next_due <= 今日）
#   POST /cards/{card_id}/review               正解→box+1 / 不正解→box=1、next_due を再計算
#
# スライス 5: Todo
#   POST/GET/PATCH/DELETE  /certifications/{cert_id}/todos など
# =========================================================================
