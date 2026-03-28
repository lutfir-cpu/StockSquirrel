
## Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/lutfir-cpu/StockSquirrel.git
cd StockSquirrel/backend
````

### 2. Create and activate a virtual environment

```bash
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

### 3. Install dependencies

```bash
pip install fastapi uvicorn openai pydantic-settings python-dotenv httpx
```

### 4. Set up environment variables

Create a `.env` file in the backend folder:

```env
NEEED TO UPDATE THIS
```

### 5. Run the FastAPI server

```bash
uvicorn main:app --reload
```

### 6. Open the app

Once the server is running, open:

* API root: `http://127.0.0.1:8000`
* Swagger docs: `http://127.0.0.1:8000/docs`

