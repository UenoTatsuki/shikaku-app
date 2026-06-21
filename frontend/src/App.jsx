import { useState, useEffect } from "react";
import CertificationDetail from "./CertificationDetail";

const API = "http://localhost:8000";

function App() {
  const [certifications, setCertifications] = useState([]);
  const [name, setName] = useState("");
  const [examDate, setExamDate] = useState("");
  const [selectedCert, setSelectedCert] = useState(null);

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

  return (
    <div className="page">
      <h1 className="app-title">資格学習アプリ</h1>
      <p className="app-subtitle">資格の管理・勉強時間・暗記カードをまとめて</p>

      <div className="card">
        <h2>資格を追加</h2>
        <div className="row">
          <input type="text" placeholder="資格名" value={name}
            onChange={(e) => setName(e.target.value)} />
          <input type="date" value={examDate}
            onChange={(e) => setExamDate(e.target.value)} />
          <button onClick={handleCreate}>追加</button>
        </div>
      </div>

      <div className="card">
        <h2>資格一覧</h2>
        {certifications.length === 0 ? (
          <p className="muted">まだ資格がありません。</p>
        ) : (
          <ul className="cert-list">
            {certifications.map((cert) => (
              <li key={cert.id} className="cert-item">
                <span>
                  {cert.name}
                  {cert.days_until_exam !== null && (
                    <span className="cert-days">試験まであと {cert.days_until_exam} 日</span>
                  )}
                </span>
                <button className="secondary" onClick={() => setSelectedCert(cert)}>選択</button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {selectedCert && <CertificationDetail cert={selectedCert} />}
    </div>
  );
}

export default App;