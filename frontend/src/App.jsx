import { useState } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [ticker, setTicker] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function analyze() {
    setAnalysis(null);
    setError(null);
    setLoading(true);

    try {
      const response = await axios.post("/analyze", { ticker });
      setAnalysis(response.data);
    } catch (err) {
      console.error("Error analyzing stock:", err);
      setError("Failed to analyze.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <h1> StockSquirrel </h1>

      <input
        value={ticker}
        onChange={(e) => setTicker(e.target.value)}
        placeholder="ticker"
      />

      <button onClick={analyze} disabled={loading}>
        {loading ? "Analyzing..." : "Analyze"}
      </button>

      {error && <div className="error">{error}</div>}

      {analysis && 
          <pre>{JSON.stringify(analysis, null, 2)}</pre>
       
      }
    </>
  );
}

export default App;
