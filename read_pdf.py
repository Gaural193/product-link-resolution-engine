import pypdf

def extract_text(pdf_path):
    reader = pypdf.PdfReader(pdf_path)
    text = []
    for page in reader.pages:
        text.append(page.extract_text())
    return "\n".join(text)

with open("output.txt", "w", encoding="utf-8") as f:
    f.write(extract_text("task.pdf"))
