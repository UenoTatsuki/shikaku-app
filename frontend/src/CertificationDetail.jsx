import { useState, useEffect } from "react";

const API = "http://localhost:8000";

function CertificationDetail({ cert }) {
  const [sessionData, setSessionData] = useState(null);
  const [minutes, setMinutes] = useState("");

  const [dueCards, setDueCards] = useState([]);
  const [revealed, setRevealed] = useState(false);
  const [newQuestion, setNewQuestion] = useState("");
  const [newAnswer, setNewAnswer] = useState("");

  const [textbooks, setTextbooks] = useState([]);
  const [newBookTitle, setNewBookTitle] = useState("");

  const [todos, setTodos] = useState([]);
  const [newTodoTitle, setNewTodoTitle] = useState("");

  useEffect(() => {
    setRevealed(false);
    loadSessions();
    loadDueCards();
    loadTextbooks();
    loadTodos();
  }, [cert.id]);

  const loadSessions = () => {
    fetch(`${API}/certifications/${cert.id}/sessions`)
      .then((res) => res.json()).then((data) => setSessionData(data))
      .catch((err) => console.error("学習記録の取得に失敗:", err));
  };

  const handleAddSession = () => {
    const m = parseInt(minutes, 10);
    if (!m || m <= 0) { alert("勉強した分数を入力してください"); return; }
    fetch(`${API}/certifications/${cert.id}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration_min: m }),
    })
      .then((res) => res.json())
      .then(() => { setMinutes(""); loadSessions(); })
      .catch((err) => console.error("記録に失敗:", err));
  };

  const loadDueCards = () => {
    fetch(`${API}/certifications/${cert.id}/cards/due`)
      .then((res) => res.json()).then((data) => setDueCards(data))
      .catch((err) => console.error("カードの取得に失敗:", err));
  };

  const handleAddCard = () => {
    if (newQuestion === "" || newAnswer === "") { alert("問題と答えの両方を入力してください"); return; }
    fetch(`${API}/certifications/${cert.id}/cards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: newQuestion, answer: newAnswer }),
    })
      .then((res) => res.json())
      .then(() => { setNewQuestion(""); setNewAnswer(""); loadDueCards(); })
      .catch((err) => console.error("カード追加に失敗:", err));
  };

  const handleReview = (correct) => {
    const card = dueCards[0];
    fetch(`${API}/cards/${card.id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ correct }),
    })
      .then((res) => res.json())
      .then(() => { setRevealed(false); loadDueCards(); })
      .catch((err) => console.error("復習の記録に失敗:", err));
  };

  const loadTextbooks = () => {
    fetch(`${API}/certifications/${cert.id}/textbooks`)
      .then((res) => res.json()).then((data) => setTextbooks(data))
      .catch((err) => console.error("参考書の取得に失敗:", err));
  };

  const handleAddTextbook = () => {
    if (newBookTitle === "") { alert("参考書名を入力してください"); return; }
    fetch(`${API}/certifications/${cert.id}/textbooks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newBookTitle }),
    })
      .then((res) => res.json())
      .then(() => { setNewBookTitle(""); loadTextbooks(); })
      .catch((err) => console.error("参考書追加に失敗:", err));
  };

  const handleNextChapter = (book) => {
    fetch(`${API}/textbooks/${book.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_chapter: book.current_chapter + 1 }),
    })
      .then((res) => res.json())
      .then(() => loadTextbooks())
      .catch((err) => console.error("進捗更新に失敗:", err));
  };

  const loadTodos = () => {
    fetch(`${API}/certifications/${cert.id}/todos`)
      .then((res) => res.json()).then((data) => setTodos(data))
      .catch((err) => console.error("Todoの取得に失敗:", err));
  };

  const handleAddTodo = () => {
    if (newTodoTitle === "") { alert("タスクを入力してください"); return; }
    fetch(`${API}/certifications/${cert.id}/todos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTodoTitle }),
    })
      .then((res) => res.json())
      .then(() => { setNewTodoTitle(""); loadTodos(); })
      .catch((err) => console.error("Todo追加に失敗:", err));
  };

  const handleToggleTodo = (todo) => {
    fetch(`${API}/todos/${todo.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_done: !todo.is_done }),
    })
      .then((res) => res.json())
      .then(() => loadTodos())
      .catch((err) => console.error("Todo更新に失敗:", err));
  };

  const currentCard = dueCards[0];

  return (
    <div className="card">
      <h2>{cert.name}</h2>

      <h3>勉強時間</h3>
      <p>
        <span className="stat">{sessionData ? sessionData.total_min : 0}</span>
        <span className="stat-label"> 分</span>
      </p>
      <div className="row">
        <input type="number" placeholder="分" value={minutes}
          onChange={(e) => setMinutes(e.target.value)} />
        <button onClick={handleAddSession}>記録</button>
      </div>

      <h3>カードを追加</h3>
      <div className="row">
        <input type="text" placeholder="問題" value={newQuestion}
          onChange={(e) => setNewQuestion(e.target.value)} />
        <input type="text" placeholder="答え" value={newAnswer}
          onChange={(e) => setNewAnswer(e.target.value)} />
        <button onClick={handleAddCard}>追加</button>
      </div>

      <h3>今日の復習（残り {dueCards.length} 枚）</h3>
      {currentCard ? (
        <div className="flashcard">
          <p className="question">{currentCard.question}</p>
          {revealed ? (
            <>
              <p className="answer">{currentCard.answer}</p>
              <div className="row" style={{ justifyContent: "center" }}>
                <button onClick={() => handleReview(true)}>正解</button>
                <button className="secondary" onClick={() => handleReview(false)}>不正解</button>
              </div>
            </>
          ) : (
            <button onClick={() => setRevealed(true)}>答えを見る</button>
          )}
        </div>
      ) : (
        <p className="muted">今日の復習は完了です。お疲れさまでした。</p>
      )}

      <h3>参考書</h3>
      <div className="row">
        <input type="text" placeholder="参考書名" value={newBookTitle}
          onChange={(e) => setNewBookTitle(e.target.value)} />
        <button onClick={handleAddTextbook}>追加</button>
      </div>
      <ul className="item-list">
        {textbooks.map((book) => (
          <li key={book.id}>
            <span style={{ flex: 1 }}>{book.title} ── {book.current_chapter} 章まで</span>
            <button className="secondary" onClick={() => handleNextChapter(book)}>次の章へ</button>
          </li>
        ))}
      </ul>

      <h3>やること（Todo）</h3>
      <div className="row">
        <input type="text" placeholder="タスク" value={newTodoTitle}
          onChange={(e) => setNewTodoTitle(e.target.value)} />
        <button onClick={handleAddTodo}>追加</button>
      </div>
      <ul className="item-list">
        {todos.map((todo) => (
          <li key={todo.id}>
            <input type="checkbox" checked={todo.is_done}
              onChange={() => handleToggleTodo(todo)} />
            <span className={todo.is_done ? "done" : ""}>{todo.title}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default CertificationDetail;