from __future__ import annotations
import argparse
import os
from pathlib import Path
from typing import List

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from config import settings


ALLOWED_EXTS = {
    ".txt", ".md", ".rst", ".log", ".cfg", ".ini", ".toml", ".yaml", ".yml",
    ".py", ".json", ".csv",
}


def iter_text_files(paths: List[str]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        path = Path(p)
        if not path.exists():
            print(f"[skip] not found: {path}")
            continue
        if path.is_file():
            if path.suffix.lower() in ALLOWED_EXTS and "__pycache__" not in str(path):
                files.append(path)
            else:
                print(f"[skip] not a text file: {path}")
            continue
        # directory
        for f in path.rglob("*"):
            if not f.is_file():
                continue
            if "__pycache__" in f.parts or f.suffix.lower() not in ALLOWED_EXTS:
                continue
            files.append(f)
    return files


def load_paths(paths: List[str]) -> list:
    docs = []
    files = iter_text_files(paths)
    print(f"[info] loading {len(files)} text files...")
    for f in files:
        try:
            loader = TextLoader(str(f), encoding="utf-8", autodetect_encoding=True)
        except TypeError:
            loader = TextLoader(str(f), encoding="utf-8")  # older versions
        try:
            docs.extend(loader.load())
        except Exception as e:
            print(f"[warn] failed to load {f}: {e}")
    return docs


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest files/directories into a FAISS index for RAG")
    parser.add_argument("paths", nargs="+", help="Files or directories to ingest")
    args = parser.parse_args()

    raw_docs = load_paths(args.paths)
    if not raw_docs:
        print("No documents loaded. Exiting.")
        return

    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    docs = splitter.split_documents(raw_docs)

    embeddings = HuggingFaceEmbeddings(model_name=settings.embedding_model)
    vs = FAISS.from_documents(docs, embedding=embeddings)

    out_dir = Path(settings.index_path)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    vs.save_local(str(out_dir))
    print(f"Saved FAISS index to: {out_dir}")


if __name__ == "__main__":
    main()
