"""Prepare the LMS data for analysis.

Reads the raw Excel files in data/raw/ and writes cleaned CSVs to data/processed/.
The cleaned table reproduces the figures in the Power BI report:
44 enrollments, 30 students, average score 77.86.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
PASS_MARK = 60  # lowest Passed score in the data is 62, highest Failed score is 55


def clean_students(s: pd.DataFrame) -> pd.DataFrame:
    s = s.copy()
    # Missing Student_IDs follow the ST001..ST030 sequence, so restore them by position
    expected = [f"ST{i:03d}" for i in range(1, len(s) + 1)]
    s["Student_ID"] = s["Student_ID"].fillna(pd.Series(expected, index=s.index))
    for col in ["Gender", "City", "Program"]:
        s[col] = s[col].fillna("Unknown")
    return s


def clean_enrollments(e: pd.DataFrame) -> pd.DataFrame:
    e = e.drop_duplicates()                       # 2 exact duplicate rows
    e = e.dropna(subset=["Enrollment_ID"])        # 6 rows without an Enrollment_ID
    e = e.copy()
    e["Enrollment_Date"] = pd.to_datetime(e["Enrollment_Date"])
    # Status is derived from Score so every row has one
    e["Status_orig"] = e["Status"]
    e["Status"] = e["Score"].apply(
        lambda x: None if pd.isna(x) else ("Passed" if x >= PASS_MARK else "Failed"))
    # Rows with no Score keep their original Status (all are Passed)
    e["Status"] = e["Status"].fillna(e["Status_orig"])
    return e.drop(columns="Status_orig").reset_index(drop=True)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    students = clean_students(pd.read_excel(RAW / "Students.xlsx"))
    courses = pd.read_excel(RAW / "Courses.xlsx")
    enroll = clean_enrollments(pd.read_excel(RAW / "Enrollments.xlsx"))

    table = (enroll.merge(students, on="Student_ID", how="left")
                   .merge(courses, on="Course_ID", how="left"))
    table = table.rename(columns={"Program": "Student_Program",
                                  "Course_Name": "Course_Title",
                                  "Department": "Course_Program"})

    students.to_csv(OUT / "students_clean.csv", index=False)
    courses.to_csv(OUT / "courses_clean.csv", index=False)
    enroll.to_csv(OUT / "enrollments_clean.csv", index=False)
    table.to_csv(OUT / "lms_analysis_table.csv", index=False)

    print(f"Students: {len(students)} | Enrollments: {len(enroll)} | "
          f"Average score: {enroll['Score'].mean():.2f}")


if __name__ == "__main__":
    main()
