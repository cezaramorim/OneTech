from __future__ import annotations

import argparse
import sys
from pathlib import Path

DEFAULT_EXTENSIONS = {
    ".py",
    ".html",
    ".css",
    ".js",
    ".json",
    ".md",
    ".txt",
}
DEFAULT_EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "staticfiles",
    "media",
    "__pycache__",
}
MOJIBAKE_MARKERS = ("Ã", "Â", "�")


def iter_files(root: Path, extensions: set[str]) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in DEFAULT_EXCLUDE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in extensions:
            files.append(path)
    return files


def find_mojibake_lines(path: Path) -> list[tuple[int, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return [(-1, "Arquivo nao e UTF-8 valido")]

    matches: list[tuple[int, str]] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if any(marker in line for marker in MOJIBAKE_MARKERS):
            matches.append((line_no, line.strip()))
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(description="Detecta texto corrompido (mojibake) em arquivos do projeto.")
    parser.add_argument("path", nargs="?", default=".", help="Diretorio raiz para varredura")
    parser.add_argument("--max-per-file", type=int, default=10, help="Maximo de linhas exibidas por arquivo")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    files = iter_files(root, DEFAULT_EXTENSIONS)
    findings = 0

    for path in files:
        matches = find_mojibake_lines(path)
        if not matches:
            continue
        findings += 1
        print(f"\n[{path}]")
        for line_no, line in matches[: args.max_per_file]:
            if line_no == -1:
                print(f"  ! {line}")
            else:
                safe_line = line.encode('ascii', 'backslashreplace').decode('ascii')
                print(f"  {line_no}: {safe_line}")
        if len(matches) > args.max_per_file:
            remaining = len(matches) - args.max_per_file
            print(f"  ... mais {remaining} linha(s)")

    if findings == 0:
        print("Nenhum padrao de mojibake encontrado.")
        return 0

    print(f"\nArquivos com indicios de mojibake: {findings}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
