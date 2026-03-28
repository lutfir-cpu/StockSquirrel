import { useState, useEffect } from "react";
import axios from "axios";
import AnalysisCard from "../components/AnalysisCard";
import "./TickerAnalysis.css";

function TickerAnalysis() {
  const [ticker, setTicker] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validTickers, setValidTickers] = useState(null);
  const [tickersLoading, setTickersLoading] = useState(true); // NEW: track ticker list load state

  async function analyze(tickerToAnalyze) { // accept ticker as param to avoid stale closure
    setAnalysis(null);
    setError(null);
    setLoading(true);

    try {
      const response = await axios.post("/analyze", { ticker: tickerToAnalyze });
      setAnalysis(response.data);
    } catch (err) {
      console.error("Error analyzing stock:", err);
      setError("Failed to analyze.");
    } finally {
      setLoading(false);
    }
  }

  function handleAnalyze() {
    if (loading) return;
    setError(null);

    const trimmed = ticker.trim().toUpperCase(); // normalize before validation

    if (!trimmed) {
      setError("Please enter a ticker");
      return;
    }

    // Guard: ticker list still loading
    if (tickersLoading) {
      
      setError("Still loading valid tickers, please try again shortly.");
      return;
    }

    // Guard: ticker list failed to load
    if (!validTickers) {
      setError("Could not load ticker list. Please refresh the page.");
      return;
    }

    if (!validTickers.has(trimmed)) {
      setError(`"${trimmed}" is not a valid SEC-listed ticker.`);
      return;
    }

    analyze(trimmed);
  }

  useEffect(() => {
    let cancelled = false;

    async function loadTickers() {
      setTickersLoading(true);
      try {
        const res = await axios.get("/tickers"); // proxy to https://www.sec.gov/files/company_tickers.json
        const data = res.data;
        console.log("Loaded tickers:", data); 

        // SEC format: { "0": { cik_str, ticker, title }, "1": {...}, ... }
        const set = new Set(
          Object.values(data)
          .filter((it) => it?.ticker)
          .map((it) => it.ticker.toUpperCase().trim()) // normalize on load
        );

        if (!cancelled) {
          setValidTickers(set);
          setTickersLoading(false);
        }
      } catch (err) {
        console.error("Error loading SEC tickers:", err);
        if (!cancelled) {
          setValidTickers(null);
          setTickersLoading(false);
        }
      }
    }

    loadTickers();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="ticker-analysis-page">
      <div className="page-header">
        <h2>Ticker Analysis</h2>
        <p>Enter a stock ticker to get detailed analysis.</p>
      </div>

      <div className="search-wrapper">
        <div className="search-container">
          <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="8"></circle>
            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
          </svg>

          <input
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder={tickersLoading ? "Loading tickers..." : "Search for a stock ticker"} // NEW: feedback while loading
            disabled={tickersLoading} // NEW: prevent input until tickers are ready
            onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
          />
        </div>

        <button onClick={handleAnalyze} disabled={loading || tickersLoading}> {/* NEW: disable during ticker load too */}
          <span className="acorn-button">🌰</span>
        </button>
      </div>

      {loading && (
        <div className="loading-state">
          <img src="/pinksquirrel.svg" className="bouncing-squirrel" />
          <p>Foraging information...</p>
        </div>
      )}

      <div className="analysis-result">
        {error && <div className="error">{error}</div>}
        {analysis && <AnalysisCard analysis={analysis} />}
      </div>
    </div>
  );
}

export default TickerAnalysis;