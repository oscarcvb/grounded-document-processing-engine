from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from io import BytesIO
from openpyxl import load_workbook
from google import genai
import os
import time

app = FastAPI()

templates = Jinja2Templates(directory="templates")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def answer_question(question: str, context_text: str) -> str:
    prompt = f"""
You are answering a question using only the provided context.

Rules:
- Answer only from the provided context.
- Do not use outside knowledge.
- If the answer is not explicitly contained in the context, return exactly:
Insufficient information
- Keep the answer concise.

Context:
{context_text}

Question:
{question}
"""

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        answer = response.text.strip() if response.text else ""

        if not answer:
            return "Insufficient information"

        return answer

    except Exception as e:
        print(f"Gemini call failed for question: {question}")
        print(f"Error: {e}")
        return "Insufficient information"

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):

    #validate the file format
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported")

    #validate file has at least 2 sheets
    excel_file = pd.ExcelFile(file.file)
    if len(excel_file.sheet_names) < 2:
        raise HTTPException(status_code=400, detail="Workbook must contain at least 2 sheets")

    #reset stream to ensure reading sheets from the beginning 
    file.file.seek(0)

    #read Excel from stream
    if "Questions" not in excel_file.sheet_names:
        raise HTTPException(status_code=400, detail="Sheet 'Questions' not found")
    df_sheet_a=pd.read_excel(file.file, sheet_name='Questions')
    if df_sheet_a.empty:
        raise HTTPException(status_code=400, detail="Sheet 'Questions' is empty")

    file.file.seek(0)

    #reset stream to read sheet 1
    if "Context" not in excel_file.sheet_names:
        raise HTTPException(status_code=400, detail="Sheet 'Context' not found")
    df_sheet_b=pd.read_excel(file.file, sheet_name='Context', header=None)
    if df_sheet_b.empty:
        raise HTTPException(status_code=400, detail="Sheet 'Context' is empty")

    questions = [str(x).strip() for x in df_sheet_a["Question"].dropna().tolist() if str(x).strip()]
    if not questions:
        raise HTTPException(status_code=400, detail="Sheet 'Questions' is empty")
        
    if len(questions) > 5:
        raise HTTPException(
            status_code=400,
            detail="A maximum of 5 questions is supported per workbook in this demo."
    )

    context_lines = [str(x).strip() for x in df_sheet_b[0].dropna().tolist() if str(x).strip()]
    if not context_lines:
        raise HTTPException(status_code=400, detail="Sheet 'Context' is empty")

    context_text = "\n".join(context_lines)
    answers=[]

    for index, question in enumerate(questions):
        answer = answer_question(question, context_text)

        if answer == "Insufficient information":
            status = "review_required"
        else:
            status = "answered"

        answers.append({
            "question": question,
            "answer": answer,
            "status": status
        })

        if index < len(questions) - 1:
            time.sleep(1)


    file.file.seek(0)
    workbook=load_workbook(file.file)
    sheet=workbook["Questions"]

    for row_index, item in enumerate(answers, start=2):
        sheet[f"C{row_index}"]=item["answer"]
        sheet[f"D{row_index}"]=item["status"]

    output=BytesIO()
    workbook.save(output)
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=answered_workbook.xlsx"}
    )