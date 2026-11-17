# AI Text Summarizer — Viva Questions and Answers

Use these as preparation notes. Explain the behavior you can demonstrate on your own machine and avoid claiming a live provider test unless you have actually run one.

1. **What problem does this project address?**  
   It helps users condense pasted text or selectable text from a PDF into a shorter summary and retrieve past results locally.

2. **What is the technology stack?**  
   React and Vite provide the browser interface. FastAPI and Pydantic provide the Python API and validation. `pypdf` extracts PDF text, SQLite stores history, and Gemini or optional Ollama generates summaries.

3. **Why is the application split into frontend and backend?**  
   The frontend handles interaction and display. The backend validates requests, keeps the Gemini key out of browser code, calls providers, extracts PDF text, and manages storage.

4. **What happens when the user selects Generate Summary?**  
   The frontend posts text, length, and provider to `/api/summarize`. The backend validates and trims the text, calls the selected adapter, counts words, saves a successful result, and returns it to the frontend.

5. **Which summary lengths are supported?**  
   `short`, `medium`, and `long`. The prompt suggests approximately 20–25%, 35–40%, and 50–60% of source length respectively; the code does not enforce those ratios.

6. **How is the provider selected?**  
   The UI offers Google Gemini and Ollama. The API request uses `gemini` or `ollama`, and the backend dispatches to the corresponding service function.

7. **Where is the Gemini API key stored?**  
   In `backend/.env` as `GEMINI_API_KEY`. The backend loads it through `python-dotenv`; it should not be committed or placed in frontend code.

8. **What is the purpose of `GEMINI_MODEL`?**  
   It selects the Gemini model requested by the backend. The code defaults to `gemini-3-flash-preview`, but usable models and quotas depend on the API project.

9. **Does Ollama work without setup?**  
   No. Ollama must be installed and running locally, and the model named by `OLLAMA_MODEL` must be available. The app calls its local `/api/generate` endpoint.

10. **What does the health endpoint check?**  
    `GET /api/health` confirms the FastAPI application responds. It does not check whether Gemini credentials or Ollama are working.

11. **How is a PDF processed?**  
    The upload route checks filename, MIME type, size, and nonempty content. `pypdf` reads it from memory, extracts selectable page text, and returns text plus page and word counts.

12. **Why are scanned PDFs unsupported?**  
    They usually contain page images rather than selectable text. This project has no OCR step, so `pypdf` cannot recover their words.

13. **Are uploaded PDFs saved?**  
    The PDF route reads the uploaded file in memory and does not save the file. If the extracted text is later summarized, that source text is stored in SQLite history.

14. **What input limits are implemented?**  
    The default PDF upload limit is 5 MB. PDF extracted text and summary input are limited to 50,000 characters. The upload limit can be set with `PDF_MAX_UPLOAD_BYTES`.

15. **What happens for blank or oversized text?**  
    Blank text returns HTTP `400`; text over 50,000 characters returns HTTP `413`. Pydantic also validates request field types and allowed values.

16. **How are word counts calculated?**  
    The backend uses Python `split()` on whitespace for original and summary text. This is a simple display metric, not a language-aware tokenizer.

17. **Where is history stored?**  
    In local SQLite at `backend/data/history.sqlite3` by default. `HISTORY_DB_PATH` can override the location.

18. **What does a history record contain?**  
    Its ID, full original text, summary, chosen length and provider, both word counts, and a UTC creation timestamp.

19. **When is a history record created?**  
    After a provider successfully returns a nonempty summary. A handled provider failure does not reach the save operation.

20. **How can a user manage history?**  
    The UI lists records, restores a selected record to the input and output areas, deletes one record, or clears all records after confirmation.

21. **Why use parameterized SQL queries?**  
    They keep user text as SQL values rather than executable SQL syntax. The history service uses placeholders for insert, fetch by ID, and delete by ID.

22. **What is CORS doing here?**  
    It allows the local Vite frontend to call the FastAPI server from a different local port. The configured rule accepts `localhost` or `127.0.0.1` origins with ports beginning `517`.

23. **How does the app handle prompt injection in source text?**  
    The prompts mark source text as data and instruct the model not to obey commands inside it. This reduces risk but does not guarantee the model will always comply.

24. **What tests have actually passed?**  
    On 17 November 2026, three backend unit tests for history passed and the frontend Vite production build succeeded. The unit tests mock both provider responses; they are not live Gemini or Ollama tests.

25. **What are the most important limitations and next steps?**  
    Generated summaries need human review, OCR is absent, provider access depends on external/local setup, and history has no encryption or user accounts. Useful next steps include OCR, browser and provider integration tests, and history search or retention controls.
