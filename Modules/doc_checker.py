import os
from langchain_community.document_loaders import Docx2txtLoader, PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def read_document(file_path):
    """Reads .docx or .pdf and returns text."""
    if file_path.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
    elif file_path.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    else:
        raise ValueError("Unsupported format")
    docs = loader.load()
    return " ".join([d.page_content for d in docs])


def check_document_sensitivity(text):
    """Classify doc text as sensitive or not."""
    keywords = ["confidential", "secret", "salary", "internal use only"]
    if any(k in text.lower() for k in keywords):
        return True
    return False


def classify_document(file_path):
    """Combined helper."""
    text = read_document(file_path)
    sensitive = check_document_sensitivity(text)
    return {"sensitive": sensitive, "length": len(text)}


if __name__ == "__main__":
    # Quick test — adjust path
    result = classify_document("test.docx")
    print("Classification:", result)
