"""FastAPI 本体。

今はスライス 1（資格の登録・一覧・詳細・更新・削除＋試験日カウントダウン）
だけを実装している。スライス 2 以降は、この下に同じ書き方で
エンドポイントを足していく（末尾の TODO メモ参照）。

起動方法は README.md を参照。起動後 http://127.0.0.1:8000/docs を開くと、
ブラウザ上で全 API を試せる（FastAPI が自動で用意してくれる画面）。
"""

from datetime import date
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, SQLModel, select

from .database import init_db, get_session
from .models import Certification

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
