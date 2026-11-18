"""Charts for the LMS enrollment analysis (reads data/processed/ and writes visuals/)."""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / "data" / "processed"
OUT = ROOT / "visuals"

GREEN, DARK, LIGHT, ORANGE, RED, GREY = "#1E9E78", "#0B5D4B", "#8FD3BC", "#E07B39", "#C44E52", "#8C8C8C"
plt.rcParams.update({"figure.dpi": 120, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold",
                     "axes.titlecolor": DARK})


def save(name):
    plt.tight_layout()
    plt.savefig(OUT / name)
    plt.close()


def hbar(series, title, name, fmt="{:.0f}", color=GREEN, xlabel=""):
    s = series.sort_values()
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.barh(s.index, s.values, color=color)
    for i, v in enumerate(s.values):
        ax.text(v, i, " " + fmt.format(v), va="center", fontsize=9)
    ax.set_xlim(0, s.max() * 1.15)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    save(name)


def main():
    OUT.mkdir(exist_ok=True)
    t = pd.read_csv(PROC / "lms_analysis_table.csv", parse_dates=["Enrollment_Date"])
    students = pd.read_csv(PROC / "students_clean.csv")
    courses = pd.read_csv(PROC / "courses_clean.csv")

    hbar(t.groupby("Course_Title").size(), "Enrollments by Course", "enrollments_by_course.png")
    hbar(t.groupby("Course_Title")["Score"].mean(), "Average Score by Course",
         "avg_score_by_course.png", fmt="{:.1f}", color=DARK)
    hbar(t.groupby("Course_Title")["Attendance_Rate"].mean(), "Average Attendance Rate by Course (%)",
         "avg_attendance_by_course.png", fmt="{:.1f}%", color=LIGHT)
    hbar(students["Program"].value_counts(), "Students by Program", "students_by_program.png")
    hbar(t.groupby("Course_Program").size(), "Enrollments by Course Department",
         "enrollments_by_department.png")
    hbar(students["City"].value_counts(), "Students by City", "students_by_city.png")

    # Pass / fail
    s = t["Status"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(s.index, s.values, color=[GREEN, RED][:len(s)], width=0.5)
    for i, v in enumerate(s.values):
        ax.text(i, v, f"{v} ({v / s.sum() * 100:.1f}%)", ha="center", va="bottom")
    ax.set_ylim(0, s.max() * 1.15)
    ax.set_ylabel("Enrollments")
    ax.set_title("Pass vs Fail (44 enrollments)")
    save("pass_fail.png")

    # Score distribution
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(t["Score"].dropna(), bins=range(40, 101, 5), color=GREEN, edgecolor="white")
    ax.axvline(t["Score"].mean(), color=ORANGE, ls="--", label=f"Mean {t['Score'].mean():.2f}")
    ax.set_xlabel("Score")
    ax.set_ylabel("Enrollments")
    ax.set_title("Score Distribution")
    ax.legend(frameon=False)
    save("score_distribution.png")

    # Attendance vs score
    d = t.dropna(subset=["Score"])
    r = d["Score"].corr(d["Attendance_Rate"])
    z = np.polyfit(d["Attendance_Rate"], d["Score"], 1)
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(d["Attendance_Rate"], d["Score"], color=GREEN, s=45, alpha=0.8)
    xs = np.linspace(d["Attendance_Rate"].min(), d["Attendance_Rate"].max(), 50)
    ax.plot(xs, np.polyval(z, xs), color=ORANGE, lw=2)
    ax.set_xlabel("Attendance rate (%)")
    ax.set_ylabel("Score")
    ax.set_title(f"Attendance vs Score (correlation r = {r:.2f})")
    save("attendance_vs_score.png")

    # Course level
    lv = t.groupby("Course_Level")["Score"].mean()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar(lv.index, lv.values, color=[LIGHT, DARK], width=0.5)
    for i, v in enumerate(lv.values):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom")
    ax.set_ylim(0, 100)
    ax.set_title("Average Score by Course Level")
    save("score_by_level.png")

    hbar(t.groupby("Instructor")["Score"].mean(), "Average Score by Instructor",
         "score_by_instructor.png", fmt="{:.1f}", color=DARK)

    # Top students
    top = t.groupby("Student_Name")["Score"].mean().nlargest(10)
    hbar(top, "Top 10 Students by Average Score", "top_students.png", fmt="{:.1f}", color=DARK)

    # Enrollment timeline
    tl = t.dropna(subset=["Enrollment_Date"]).groupby("Enrollment_Date").size().cumsum()
    fig, ax = plt.subplots(figsize=(9, 4.3))
    ax.step(tl.index, tl.values, where="post", color=GREEN, lw=2.5)
    ax.fill_between(tl.index, tl.values, step="post", color=GREEN, alpha=0.15)
    ax.set_title("Cumulative Enrollments (Jan - Feb 2026)")
    ax.set_ylabel("Enrollments")
    fig.autofmt_xdate()
    save("cumulative_enrollments.png")

    # Demographics
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    g = students["Gender"].value_counts()
    axs[0].bar(g.index, g.values, color=[GREEN, DARK, GREY][:len(g)], width=0.55)
    for i, v in enumerate(g.values):
        axs[0].text(i, v, str(v), ha="center", va="bottom")
    axs[0].set_title("Students by Gender")
    axs[1].hist(students["Age"], bins=range(19, 29), color=GREEN, edgecolor="white")
    axs[1].set_title(f"Age Distribution (mean {students['Age'].mean():.1f})")
    axs[1].set_xlabel("Age")
    save("student_demographics.png")

    # Course x program heatmap (student program vs course department)
    h = t[t["Student_Program"] != "Unknown"].pivot_table(
        index="Student_Program", columns="Course_Program", values="Enrollment_ID", aggfunc="count", fill_value=0)
    fig, ax = plt.subplots(figsize=(8.5, 4.8))
    ax.imshow(h.values, cmap="Greens")
    ax.set_xticks(range(h.shape[1]))
    ax.set_xticklabels(h.columns, rotation=20, ha="right")
    ax.set_yticks(range(h.shape[0]))
    ax.set_yticklabels(h.index)
    for i in range(h.shape[0]):
        for j in range(h.shape[1]):
            ax.text(j, i, h.values[i, j], ha="center", va="center",
                    color="white" if h.values[i, j] > h.values.max() * 0.6 else "black")
    ax.set_title("Enrollments: Student Program x Course Department")
    ax.set_xlabel("Course department")
    ax.set_ylabel("Student program")
    save("program_vs_department_heatmap.png")

    # Enrolled vs not enrolled
    enrolled = students["Student_ID"].isin(t["Student_ID"]).sum()
    print(f"Charts saved -> {OUT} | enrolled students: {enrolled}/{len(students)} | r={r:.2f}")


if __name__ == "__main__":
    main()
