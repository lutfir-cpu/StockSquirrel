import { useState } from "react";
import axios from "axios";
import "./TickerAnalysis.css";

function TickerAnalysis() {
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
    <div className="ticker-analysis-page">

      <div className="page-header">
        <h2> Ticker Analysis </h2>
        <p>Enter a stock ticker to get detailed analysis.</p>
      </div>

      {/* input field */}
      <div className="search-wrapper">
        <div className="search-container">
          {/* search icon */}
          <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>

          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="Search for a stock ticker"
            onKeyDown={(e) => e.key === 'Enter' && !loading && ticker && analyze()}
          />
        </div>
        <button onClick={analyze} disabled={loading}>
          <span className="acorn-button">🌰</span>
        </button>
      </div>

      {loading && (
        <div className="loading-state">
          <img src="/pinksquirrel.svg" className="bouncing-squirrel" />
          <p>Foraging information...</p>
        </div>
      )}

      {/*result*/}
      <div className="analysis-result">

      {error && <div className="error">{error}</div>}

      {analysis && 
        <pre>{JSON.stringify(analysis, null, 2)}</pre>
      }
      </div>
    </div>
  );
}

export default TickerAnalysis;