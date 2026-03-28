import "./AnalysisCard.css";

function formatConfidence(confidence) {
  if (typeof confidence !== "number" || Number.isNaN(confidence)) {
    return "N/A";
  }

  return `${Math.round(confidence * 100)}%`;
}

function getSignalTone(signal) {
  const normalizedSignal = signal?.toLowerCase();

  if (normalizedSignal === "bullish" || normalizedSignal === "positive") {
    return "positive";
  }

  if (normalizedSignal === "bearish" || normalizedSignal === "negative") {
    return "negative";
  }

  return "neutral";
}

function capitalizeSignal(signal) {
  if (!signal) {
    return "Unknown";
  }

  return signal.charAt(0).toUpperCase() + signal.slice(1);
}

function renderInlineMarkdown(text) {
  return text.split(/(\*\*.*?\*\*)/g).map((part, index) => {
    const isBold = (part.startsWith("**") && part.endsWith("**")) 
                    || (part.startsWith("*") && part.endsWith("*") && part.length > 2);

    if (isBold) {
      return <strong key={index}>{part.slice(2, -2)}</strong>;
    }

    return <span key={index}>{part}</span>;
  });
}

function parseMarkdownBlocks(text) {
  const lines = text.split(/\r?\n/);
  const blocks = [];
  let paragraphLines = [];
  let listItems = [];
  let listType = null;

  const flushParagraph = () => {
    if (paragraphLines.length === 0) {
      return;
    }

    blocks.push({
      type: "paragraph",
      text: paragraphLines.join("\n").trim(),
    });
    paragraphLines = [];
  };

  const flushList = () => {
    if (listItems.length === 0) {
      return;
    }

    blocks.push({
      type: listType,
      items: [...listItems],
    });
    listItems = [];
    listType = null;
  };

  lines.forEach((line) => {
    const trimmedLine = line.trim();
    const headingMatch = line.match(/^(#{1,6})\s+(.*)$/);
    const unorderedListMatch = line.match(/^[-*]\s+(.*)$/);
    const orderedListMatch = line.match(/^\d+\.\s+(.*)$/);
    const listContinuationMatch = line.match(/^\s{2,}(.*)$/);

    if (!trimmedLine) {
      flushParagraph();
      flushList();
      return;
    }

    if (headingMatch) {
      flushParagraph();
      flushList();
      blocks.push({
        type: "heading",
        level: Math.min(headingMatch[1].length, 4),
        text: headingMatch[2].trim(),
      });
      return;
    }

    if (unorderedListMatch) {
      flushParagraph();
      if (listType && listType !== "unordered-list") {
        flushList();
      }
      listType = "unordered-list";
      listItems.push(unorderedListMatch[1].trim());
      return;
    }

    if (orderedListMatch) {
      flushParagraph();
      if (listType && listType !== "ordered-list") {
        flushList();
      }
      listType = "ordered-list";
      listItems.push(orderedListMatch[1].trim());
      return;
    }

    if (listContinuationMatch && listItems.length > 0) {
      listItems[listItems.length - 1] = `${listItems[listItems.length - 1]}\n${listContinuationMatch[1]}`;
      return;
    }

    flushList();
    paragraphLines.push(trimmedLine);
  });

  flushParagraph();
  flushList();

  return blocks;
}

function MarkdownContent({ text, className = "" }) {
  if (!text) {
    return null;
  }

  const blocks = parseMarkdownBlocks(text);

  if (blocks.length === 0) {
    return null;
  }

  return (
    <div className={`rich-text ${className}`.trim()}>
      {blocks.map((block, index) => {
        if (block.type === "heading") {
          const HeadingTag = `h${block.level}`;
          return (
            <HeadingTag key={index} className={`rich-text-heading rich-text-heading-${block.level}`}>
              {renderInlineMarkdown(block.text)}
            </HeadingTag>
          );
        }

        if (block.type === "unordered-list") {
          return (
            <ul key={index} className="rich-text-list">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
              ))}
            </ul>
          );
        }

        if (block.type === "ordered-list") {
          return (
            <ol key={index} className="rich-text-list rich-text-list-ordered">
              {block.items.map((item, itemIndex) => (
                <li key={itemIndex}>{renderInlineMarkdown(item)}</li>
              ))}
            </ol>
          );
        }

        return (
          <p key={index} className="rich-text-paragraph">
            {renderInlineMarkdown(block.text)}
          </p>
        );
      })}
    </div>
  );
}

function AnalysisCard({ analysis, compact = false }) {
  const tone = getSignalTone(analysis.signal);
  const confidence = formatConfidence(analysis.confidence);

  return (
    <article className={`analysis-card ${compact ? "analysis-card-compact" : ""}`}>
      <header className="analysis-card-header">
        <div>
          <span className="analysis-card-kicker">Foraged outlook</span>
          <div className="analysis-card-ticker-row">
            <h3>{analysis.ticker}</h3>
            <span className={`signal-pill signal-pill-${tone}`}>
              {capitalizeSignal(analysis.signal)}
            </span>
          </div>
          <p className="analysis-card-recommendation">{analysis.recommendation}</p>
        </div>

        <div className="confidence-block">
          <span className="confidence-label">Confidence</span>
          <strong>{confidence}</strong>
        </div>
      </header>

      <section className="analysis-section">
        <h4>Summary</h4>
        <MarkdownContent text={analysis.summary} />
      </section>

      <div className="analysis-grid">
        <section className="analysis-section">
          <h4>Key Drivers</h4>
          {analysis.key_drivers.length > 0 ? (
            <ul className="analysis-list">
              {analysis.key_drivers.map((driver, index) => (
                <li key={`${analysis.ticker}-driver-${index}`}>
                  <MarkdownContent text={driver} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted-copy">No major drivers were highlighted.</p>
          )}
        </section>

        <section className="analysis-section">
          <h4>Risks</h4>
          {analysis.risks.length > 0 ? (
            <ul className="analysis-list">
              {analysis.risks.map((risk, index) => (
                <li key={`${analysis.ticker}-risk-${index}`}>
                  <MarkdownContent text={risk} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted-copy">No specific risks were listed.</p>
          )}
        </section>
      </div>

      <section className="analysis-section">
        <h4>Sources</h4>
        {analysis.sources.length > 0 ? (
          <div className="source-list">
            {analysis.sources.map((source, index) => (
              <a
                key={`${analysis.ticker}-source-${index}`}
                className="source-card"
                href={source.url}
                target="_blank"
                rel="noreferrer"
              >
                <span className="source-title">{source.title || source.url}</span>
                <MarkdownContent text={source.text} />
              </a>
            ))}
          </div>
        ) : (
          <p className="muted-copy">No supporting sources were returned.</p>
        )}
      </section>
    </article>
  );
}

export default AnalysisCard;
