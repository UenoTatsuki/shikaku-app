import { useState, useEffect } from "react";

const API = "http://localhost:8000";

function App() {
  const [certifications, setCertifications] = useState([]);
  const [name, setName] = useState("");
  const [examDate, setExamDate] = useState("");

  const [selectedCert, setSelectedCert] = useState(null);
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

  const loadCertifications = () => {
    fetch(`${API}/certifications`)
      .then((res) => res.json())
      .then((data) => setCertifications(data))
      .catch((err) => console.error("取得に失敗:", err));
  };

  useEffect(() => { loadCertifications(); }, []);

  const handleCreate = () => {
    if (name === "") { alert("資格名を入力してください"); return; }
    fetch(`${API}/certifications`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, exam_date: examDate === "" ? null : examDate, status: "studying" }),
    })
      .then((res) => res.json())
      .then(() => { setName(""); setExamDate(""); loadCertifications(); })
      .catch((err) => console.error("登録に失敗:", err));
  };

  const selectCert = (cert) => {
    setSelectedCert(cert);
    setRevealed(false);
    loadSessions(cert.id);
    loadDueCards(cert.id);
    loadTextbooks(cert.id);
    loadTodos(cert.id);
  };

  const loadSessions = (certId) => {
    fetch(`${API}/certifications/${certId}/sessions`)
      .then((res) => res.json()).then((data) => setSessionData(data))
      .catch((err) => console.error("学習記録の取得に失敗:", err));
  };

  const handleAddSession = () => {
    const m = parseInt(minutes, 10);
    if (!m || m <= 0) { alert("勉強した分数を入力してください"); return; }
    fetch(`${API}/certifications/${selectedCert.id}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ duration_min: m }),
    })
      .then((res) => res.json())
      .then(() => { setMinutes(""); loadSessions(selectedCert.id); })
      .catch((err) => console.error("記録に失敗:", err));
  };

  const loadDueCards = (certId) => {
    fetch(`${API}/certifications/${certId}/cards/due`)
      .then((res) => res.json()).then((data) => setDueCards(data))
      .catch((err) => console.error("カードの取得に失敗:", err));
  };

  const handleAddCard = () => {
    if (newQuestion === "" || newAnswer === "") { alert("問題と答えの両方を入力してください"); return; }
    fetch(`${API}/certifications/${selectedCert.id}/cards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: newQuestion, answer: newAnswer }),
    })
      .then((res) => res.json())
      .then(() => { setNewQuestion(""); setNewAnswer(""); loadDueCards(selectedCert.id); })
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
      .then(() => { setRevealed(false); loadDueCards(selectedCert.id); })
      .catch((err) => console.error("復習の記録に失敗:", err));
  };

  // 参考書
  const loadTextbooks = (certId) => {
    fetch(`${API}/certifications/${certId}/textbooks`)
      .then((res) => res.json()).then((data) => setTextbooks(data))
      .catch((err) => console.error("参考書の取得に失敗:", err));
  };

  const handleAddTextbook = () => {
    if (newBookTitle === "") { alert("参考書名を入力してください"); return; }
    fetch(`${API}/certifications/${selectedCert.id}/textbooks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newBookTitle }),
    })
      .then((res) => res.json())
      .then(() => { setNewBookTitle(""); loadTextbooks(selectedCert.id); })
      .catch((err) => console.error("参考書追加に失敗:", err));
  };

  // 章を1つ進める（PATCHで更新）
  const handleNextChapter = (book) => {
    fetch(`${API}/textbooks/${book.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_chapter: book.current_chapter + 1 }),
    })
      .then((res) => res.json())
      .then(() => loadTextbooks(selectedCert.id))
      .catch((err) => console.error("進捗更新に失敗:", err));
  };

  // Todo
  const loadTodos = (certId) => {
    fetch(`${API}/certifications/${certId}/todos`)
      .then((res) => res.json()).then((data) => setTodos(data))
      .catch((err) => console.error("Todoの取得に失敗:", err));
  };

  const handleAddTodo = () => {
    if (newTodoTitle === "") { alert("タスクを入力してください"); return; }
    fetch(`${API}/certifications/${selectedCert.id}/todos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: newTodoTitle }),
    })
      .then((res) => res.json())
      .then(() => { setNewTodoTitle(""); loadTodos(selectedCert.id); })
      .catch((err) => console.error("Todo追加に失敗:", err));
  };

  // 完了の切り替え（PATCHで更新）
  const handleToggleTodo = (todo) => {
    fetch(`${API}/todos/${todo.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ is_done: !todo.is_done }),
    })
      .then((res) => res.json())
      .then(() => loadTodos(selectedCert.id))
      .catch((err) => console.error("Todo更新に失敗:", err));
  };

  const currentCard = dueCards[0];

  return (
    <div style={{ maxWidth: 600, margin: "40px auto", fontFamily: "sans-serif" }}>
      <h1>資格一覧</h1>

      <div style={{ marginBottom: 24 }}>
        <input type="text" placeholder="資格名" value={name}
          onChange={(e) => setName(e.target.value)} style={{ marginRight: 8 }} />
        <input type="date" value={examDate}
          onChange={(e) => setExamDate(e.target.value)} style={{ marginRight: 8 }} />
        <button onClick={handleCreate}>追加</button>
      </div>

      <ul>
        {certifications.map((cert) => (
          <li key={cert.id}>
            <button onClick={() => selectCert(cert)} style={{ marginRight: 8 }}>選択</button>
            {cert.name}
            {cert.days_until_exam !== null ? ` ── あと ${cert.days_until_exam} 日` : ""}
          </li>
        ))}
      </ul>

      {selectedCert && (
        <div style={{ marginTop: 32, paddingTop: 16, borderTop: "1px solid #ccc" }}>
          <h2>{selectedCert.name}</h2>

          <p>総勉強時間：{sessionData ? `${sessionData.total_min} 分` : "読み込み中..."}</p>
          <div style={{ marginBottom: 24 }}>
            <input type="number" placeholder="分" value={minutes}
              onChange={(e) => setMinutes(e.target.value)} style={{ marginRight: 8 }} />
            <button onClick={handleAddSession}>勉強時間を記録</button>
          </div>

          <h3>カードを追加</h3>
          <div style={{ marginBottom: 24 }}>
            <input type="text" placeholder="問題" value={newQuestion}
              onChange={(e) => setNewQuestion(e.target.value)} style={{ marginRight: 8 }} />
            <input type="text" placeholder="答え" value={newAnswer}
              onChange={(e) => setNewAnswer(e.target.value)} style={{ marginRight: 8 }} />
            <button onClick={handleAddCard}>追加</button>
          </div>

          <h3>今日の復習（残り {dueCards.length} 枚）</h3>
          {currentCard ? (
            <div style={{ border: "1px solid #ccc", borderRadius: 8, padding: 16, marginBottom: 24 }}>
              <p style={{ fontWeight: "bold" }}>{currentCard.question}</p>
              {revealed ? (
                <>
                  <p>答え：{currentCard.answer}</p>
                  <button onClick={() => handleReview(true)} style={{ marginRight: 8 }}>正解</button>
                  <button onClick={() => handleReview(false)}>不正解</button>
                </>
              ) : (
                <button onClick={() => setRevealed(true)}>答えを見る</button>
              )}
            </div>
          ) : (
            <p>今日の復習は完了です。お疲れさまでした。</p>
          )}

          <h3>参考書</h3>
          <div style={{ marginBottom: 12 }}>
            <input type="text" placeholder="参考書名" value={newBookTitle}
              onChange={(e) => setNewBookTitle(e.target.value)} style={{ marginRight: 8 }} />
            <button onClick={handleAddTextbook}>追加</button>
          </div>
          <ul>
            {textbooks.map((book) => (
              <li key={book.id}>
                {book.title} ── {book.current_chapter} 章まで
                <button onClick={() => handleNextChapter(book)} style={{ marginLeft: 8 }}>次の章へ</button>
              </li>
            ))}
          </ul>

          <h3>やること（Todo）</h3>
          <div style={{ marginBottom: 12 }}>
            <input type="text" placeholder="タスク" value={newTodoTitle}
              onChange={(e) => setNewTodoTitle(e.target.value)} style={{ marginRight: 8 }} />
            <button onClick={handleAddTodo}>追加</button>
          </div>
          <ul style={{ listStyle: "none", paddingLeft: 0 }}>
            {todos.map((todo) => (
              <li key={todo.id}>
                <label>
                  <input type="checkbox" checked={todo.is_done}
                    onChange={() => handleToggleTodo(todo)} />
                  <span style={{ textDecoration: todo.is_done ? "line-through" : "none", marginLeft: 6 }}>
                    {todo.title}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

export default App;