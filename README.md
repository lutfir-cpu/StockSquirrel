
# StockSquirrel
Your real-time AI-assisted Stock Market Sentiment Analyzer <br>
Note: Not intended for formal financial advice. AI can agenerate mistakes.

<img width="1892" height="899" alt="image" src="https://github.com/user-attachments/assets/b9348270-0e84-41c2-9c73-8d38d1df279a" />

## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/lutfir-cpu/StockSquirrel.git
cd StockSquirrel
```

### 2. Set up and run the backend

```bash
cd backend
python -m venv venv
```

**On Windows**

```bash
venv\Scripts\activate
```

**On macOS/Linux**

```bash
source venv/bin/activate
```

Install backend dependencies:

```bash
pip install fastapi uvicorn openai pydantic-settings python-dotenv httpx
```

Create a `.env` file in the `backend` folder:

```env
OPENAI_API_KEY=
TINYFISH_API_KEY=
```

Run the FastAPI server:

```bash
uvicorn main:app --reload
```

The backend will be available at:

* API root: `http://127.0.0.1:8000`
* Swagger docs: `http://127.0.0.1:8000/docs`

### 3. Set up and run the frontend

Open a new terminal and go to the frontend folder:

```bash
cd StockSquirrel/frontend
```

Install frontend dependencies:

```bash
npm install
```

Start the frontend development server:

```bash
npm run dev
```

The frontend will usually be available at:

* `http://localhost:3000`
  or
* `http://localhost:5173`

depending on your frontend setup.

```
```
