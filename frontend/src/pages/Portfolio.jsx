import { useState } from "react";
import axios from "axios";
import "./Portfolio.css";

function Portfolio() {
  const [holdings, setHoldings] = useState([
    { ticker: "", shares: 0, weight: 0 }
  ]);
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const addRow = () => {
    setHoldings([...holdings, { ticker: "", shares: 0, weight: 0 }]);
  };

  const updateRow = (index, field, value) => {
    const newHoldings = [...holdings];
    if (field === "ticker") value = value.toUpperCase();
    newHoldings[index][field] = value;
    setHoldings(newHoldings);
  };

  const analyzeStock = async (ticker) => {
    setLoading(true);
    setResults([]);

    try {
      const response = await axios.post("/analyze", {ticker});
      setResults(response.data);
    } catch (err) {
      console.error("Error analyzing stock:", err);
    } finally {
      setLoading(false);
    }
  }

  const analyzeAll = async () => {
    setLoading(true);
    setResults([]);
    
    const validHoldings = holdings.filter(h => h.ticker);

    try {
      const requests = validHoldings.map(h => 
        axios.post("/analyze", { ticker: h.ticker }).then(res => res.data)
      );
      const responses = await Promise.all(requests);
      setResults(responses);
    } catch (err) {
      console.error("Error analyzing portfolio:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="portfolio-page">
      
      {/* Header */}
      <div className="header">
          <h2>My Portfolio</h2>
          <p>Track and manage your investment portfolio.</p>
      </div>

      {/* portfolio grid */}
      <div className="portfolio-grid">
        
        {/* portfolio overview */}
        <div className="overview-panel">
          <h3>Portfolio Overview</h3>

          <div className="holdings-stack">
            {holdings.map((holding, index) => (
              <div key={index} className="holding-row-card">
                <div className="holding-info-row">
                  <div className="holding-identity">
                    <div className="holding-squirrel">🐿️</div>
                    <div className="holding-inputs">
                      <div className="ticker-share-row">
                        <input 
                          className="stealth-input font-bold"
                          placeholder="TICKER"
                          value={holding.ticker}
                          onChange={(e) => updateRow(index, "ticker", e.target.value)}
                        />
                        <span className="share-text">{holding.shares} shares</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="holding-financials">
                    <div className="financial-value">
                      <input 
                        className="stealth-input text-right"
                        type="number"
                        placeholder="0"
                        value={holding.weight}
                        onChange={(e) => updateRow(index, "weight", e.target.value)}
                        style={{ width: '40px' }}
                      />%
                    </div>
                  </div>
                </div>

                <div className="allocation-section">
                  <div className="alloc-labels">
                    <span>Portfolio Allocation</span>
                    <span>{holding.weight || 0}%</span>
                  </div>
                  <div className="alloc-track">
                    <div 
                      className="alloc-fill" 
                      style={{ width: `${Math.min(holding.weight || 0, 100)}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* analysis */}
        <div className="analysis-panel">
          <h3 className="panel-title">Live AI Insights</h3>
          
          {loading && (
            <div className="loading-state">
            <img src="/pinksquirrel.svg" className="bouncing-squirrel" />
            <p>Foraging information...</p>
            </div>
         )}

          {!loading && results.length === 0 && (
            <div className="empty-state">
              <p>Click "View Analytics" to generate live insights.</p>
            </div>
          )}

          {!loading && results.length > 0 && (
            <div className="insights-list">
              {results.map((res, i) => (
                <div key={i} className="insight-card">
                  <div className="insight-header">
                    <h4>{res.ticker}</h4>
                    <span className="badge">{res.signal.toUpperCase()}</span>
                  </div>
                  <p>{res.summary}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="actions-grid">
        <button className="action-button" onClick={addRow}>
          <span>Add Stocks</span>
        </button>

        <button className="action-button" onClick={analyzeAll} disabled={loading || holdings.length === 0}>
          <span>View Analytics</span>
        </button>
      </div>

    </div>
  );
}

export default Portfolio;