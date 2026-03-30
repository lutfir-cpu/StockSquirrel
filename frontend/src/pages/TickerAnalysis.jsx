import { useState, useEffect, useRef } from "react";
import axios from "axios";
import AnalysisCard from "../components/AnalysisCard";
import "./TickerAnalysis.css";

function TickerAnalysis() {
  const [ticker, setTicker] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validTickers, setValidTickers] = useState(null);
  const [tickersLoading, setTickersLoading] = useState(true);
  const [previewUrl, setPreviewUrl] = useState("");
  const [statusMessage, setStatusMessage] = useState("");
  const eventSourceRef = useRef(null);

  function closeEventSource() {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
  }

  function analyze(tickerToAnalyze) {
    closeEventSource();
    setAnalysis(null);
    setError(null);
    setLoading(true);
    setPreviewUrl("");
    setStatusMessage("Starting analysis...");

    const stream = new EventSource(
      `/analyze/stream?ticker=${encodeURIComponent(tickerToAnalyze)}`
    );
    eventSourceRef.current = stream;

    stream.addEventListener("status", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setStatusMessage(payload.message || "Gathering evidence...");
      } catch (err) {
        console.error("Error parsing status event:", err);
      }
    });

    stream.addEventListener("preview_url", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setPreviewUrl(payload.streaming_url || "");
      } catch (err) {
        console.error("Error parsing preview event:", err);
      }
    });

    stream.addEventListener("analysis", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setAnalysis(payload.analysis || null);
        setStatusMessage("Analysis complete.");
        setPreviewUrl("");
        setLoading(false);
        closeEventSource();
      } catch (err) {
        console.error("Error parsing analysis event:", err);
        setError("Failed to parse analysis response.");
        setPreviewUrl("");
        setLoading(false);
        closeEventSource();
      }
    });

    stream.addEventListener("analysis_error", (event) => {
      try {
        const payload = JSON.parse(event.data);
        setError(payload.message || "Failed to analyze.");
      } catch {
        setError("Failed to analyze.");
      }
      setPreviewUrl("");
      setLoading(false);
      closeEventSource();
    });

    stream.onerror = () => {
      if (eventSourceRef.current) {
        setError("The live analysis stream was interrupted.");
        setPreviewUrl("");
        setLoading(false);
        closeEventSource();
      }
    };
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
      closeEventSource();
    };
  }, []);

  return (
    <div className="ticker-analysis-page">
      <div className="page-header">
        <h2>Ticker Analysis</h2>
        <p>
          Get a well-rounded, qualitative stock analysis using real-time evidence and
          insights gathered from the web.
        </p>
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
            placeholder={tickersLoading ? "Loading tickers..." : "Dont be shy... Search for a stock ticker!"} // NEW: feedback while loading
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
          <p>Foraging information ...</p>
        </div>
      )}

      {(loading || previewUrl) && (
        <div className="preview-panel">
          <div className="preview-header">
            <h3>Live Browser Preview</h3>
            <p>{previewUrl ? "TinyFish is browsing in real time." : "Waiting for live preview..."}</p>
          </div>
          <div className="preview-frame-shell">
            {previewUrl ? (
              <iframe
                className="preview-frame"
                src={previewUrl}
                title="TinyFish live browser preview"
              />
            ) : (
              <div className="preview-placeholder">Live preview will appear here in a few seconds.</div>
            )}
          </div>
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
