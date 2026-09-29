import pandas as pd

from readers import read_file


def test_reads_python_file_as_text(tmp_path):
    path = tmp_path / "code.py"
    path.write_text("print(1 + 1)")
    assert read_file(path, "") == "print(1 + 1)"


def test_reads_excel_file_as_csv(tmp_path):
    path = tmp_path / "sales.xlsx"
    pd.DataFrame({"item": ["burger", "soda"], "sales": [10, 5]}).to_excel(path, index=False)

    output = read_file(path, "")

    assert "item,sales" in output and "burger,10" in output


def test_unsupported_type_is_reported(tmp_path):
    path = tmp_path / "archive.zip"
    path.write_bytes(b"PK")
    assert "Unsupported file type '.zip'" in read_file(path, "")
