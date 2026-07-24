# Grounded Document Processing Engine

A FastAPI-based document processing pipeline that accepts structured Excel workbooks, validates workbook structure and content, extracts questions and grounding context, uses a language model to answer only from the provided context, writes answers and review statuses back into the workbook, and returns the completed file to the user.

## Why I built this

A production solution does more than simply call an LLM.

The crucial part in designing and building production-grade solutions is embedding LLMs into structured, reliable workflows through controlled extraction, grounding, validation, and write-back. This project was built to demonstrate that broader systems capability in a compact, portfolio-friendly way.

This solution focuses on:

- structured input contracts
- workbook validation
- grounding on user-provided context
- controlled failure handling
- structured write-back into a business artifact

## What the system does

The engine accepts an Excel workbook with two sheets:

- `Questions`
- `Context`

It then:

1. validates the workbook format and required sheets
2. extracts questions from the `Questions` sheet
3. extracts grounding text from the `Context` sheet
4. sends each question and grounded context to a Gemini model
5. writes the answer and processing status back into the workbook
6. returns the completed workbook as a downloadable file

## Workflow

```text
Upload workbook
↓
Validate structure and sheet requirements
↓
Extract questions + context
↓
Grounded LLM answering
↓
Assign status
↓
Write answers back into workbook
↓
Return completed workbook
```

## Workbook contract

### Sheet: `Questions`

The `Questions` sheet is expected to follow this structure:

| Column | Meaning |
|---|---|
| A | ID |
| B | Question |
| C | Answer |
| D | Status |

**Notes:**

- row 1 is the header row
- answers are written to column `C`
- statuses are written to column `D`

### Sheet: `Context`

The `Context` sheet is expected to contain grounding text in column `A`, one line per row.

The model is instructed to answer using only this sheet’s content.

## Example behavior

If the context explicitly supports an answer, the workbook is updated with:

- a concise answer in the `Answer` column
- `answered` in the `Status` column

If the answer is not supported by the context, the workbook is updated with:

- `Insufficient information` in the `Answer` column
- `review_required` in the `Status` column

## Validation and failure handling

The API validates:

- file extension must be `.xlsx`
- workbook must contain at least 2 sheets
- sheet `Questions` must exist
- sheet `Context` must exist
- both sheets must contain usable content
- workbook submissions are limited to a maximum of 5 questions in this demo

The system also includes fallback handling for model/API failures. If the provider is temporarily unavailable or the request cannot be completed, the pipeline falls back safely instead of failing the entire workbook generation process.

## Demo limitations

This project uses a free-tier Gemini model endpoint.

To keep the demo lightweight and manageable:

- workbook submissions are limited to **5 questions maximum**
- calls are deliberately paced between questions
- the project is intended as a demonstration of workflow design, not as a production-scale inference service

In a production implementation, this layer would likely be replaced with:

- a higher-throughput model tier
- asynchronous job orchestration
- stronger retry and queueing logic
- more robust answer validation

## Repo structure

```text
grounded-document-processing-engine/
├── app/
│   └── main.py
├── sample_files/
│   ├── demo_input.xlsx
│   ├── answered_workbook.xlsx
│   └── sample_question_bank.xlsx
├── screenshots/
│   ├── upload_ui.png
│   └── completed_workbook.png
├── README.md
├── requirements.txt
└── .gitignore
```

## Running locally

### 1. Create and activate a virtual environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your Gemini API key

```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Start the FastAPI app

```bash
uvicorn app.main:app --reload
```

### 5. Open Swagger UI

Open:

```text
http://127.0.0.1:8000/docs
```

Upload a workbook and download the completed result.

## Sample files

The `sample_files/` folder contains example workbooks showing:

- expected input format
- returned output format
- a sample question bank for testing

## Screenshots

The repository includes screenshots showing:

- the upload endpoint in Swagger UI
- a completed workbook with answers and statuses written back into the `Questions` sheet

## Future improvements

Possible next steps include:

- asynchronous job handling
- richer workbook styling and formatting preservation
- provider-agnostic LLM abstraction
- improved answer validation and normalization
- deployment behind a lightweight public upload interface
- support for larger grounded document sets

## What this project demonstrates

This project is meant to show the ability to:

- design structured AI-assisted workflows
- define and enforce input/output contracts
- operationalize a model behind an API
- ground generation on controlled context
- handle failure paths safely
- return structured outputs in a user-facing business format