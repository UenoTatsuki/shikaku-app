"""テーブル（データの入れ物）の定義。

仕様書「5. データモデル」に対応。資格を親に、4 種類の子要素が
certification_id でひもづく。今は全テーブルを定義しておくが、
API（main.py）はまずスライス 1 の資格ぶんだけ実装してある。
残りはスライス 2 以降で API を足していく。
"""

from datetime import date
from typing import Optional

from sqlmodel import SQLModel, Field


class Certification(SQLModel, table=True):
    """資格（このアプリの親データ）。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    exam_date: Optional[date] = None       # 試験日（未定なら空）
    status: str = "studying"               # studying = 勉強中 / acquired = 取得済み


class Flashcard(SQLModel, table=True):
    """暗記カード。Leitner 方式の box と next_due を持つ。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    question: str
    answer: str
    box: int = 1                           # 箱番号 1〜5（最初は 1）
    next_due: Optional[date] = None        # 次回出題日


class Todo(SQLModel, table=True):
    """資格ごとのタスク。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    title: str
    is_done: bool = False


class StudySession(SQLModel, table=True):
    """1 回ぶんの学習記録。総勉強時間はこの合計で出す。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    duration_min: int                      # 学習時間（分）
    studied_at: date                       # 学習日


class Textbook(SQLModel, table=True):
    """参考書と、どこまで進んだか。"""
    id: Optional[int] = Field(default=None, primary_key=True)
    certification_id: int = Field(foreign_key="certification.id")
    title: str
    current_chapter: int = 0               # 今いる章（最初は 0）
    total_chapters: Optional[int] = None   # 全章数（任意）
