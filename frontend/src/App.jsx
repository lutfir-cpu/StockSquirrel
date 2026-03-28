import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import TickerAnalysis from "./pages/tickeranalysis";
import Portfolio from "./pages/portfolio";
import "./App.css";

function App() {
  
  return (
    <BrowserRouter>

    <header className="top-nav">

      <div className="logo">
        <img src="/pinksquirrel.svg" className="logo-icon" />
        <span className="logo-text">StockSquirrel</span>
      </div>

      <nav className="tabs">
          <NavLink 
            to="/" 
            className={({ isActive }) => (isActive ? "active" : "")}
            end
          >
            Ticker Analysis
          </NavLink>
          
          <NavLink 
            to="/portfolio" 
            className={({ isActive }) => (isActive ? "active" : "")}
          >
            Portfolio
          </NavLink>
      </nav>
    </header>

    <div className="content">
      <Routes>
        <Route path="/" element={<TickerAnalysis />} />
        <Route path="/portfolio" element={<Portfolio />} />
      </Routes>
    </div>

    </BrowserRouter>
  );
}

export default App;
