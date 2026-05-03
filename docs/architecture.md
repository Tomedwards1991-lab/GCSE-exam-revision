# Architecture Notes

## Product Shape

The first version is a Django monolith with server-rendered Bootstrap templates. The product focus is WJEC GCSE Computer Science Unit 2, especially the recurring HTML and Greenfoot practical question patterns.

React is not included yet. It would make sense later for richer in-browser experiences such as drag-and-drop trace tables, code editors, live pseudocode stepping, or a more animated walkthrough wizard. For the current slice, Django templates give faster iteration and less operational surface.

## Core Concepts

- `SpecificationUnit`: expandable exam-unit boundary. The current seed focuses on `3500U20-1`.
- `Paper`: a source paper and mark scheme pair.
- `Topic`: filterable syllabus areas.
- `Question`: either `past_paper` or `generated`.
- `WalkthroughStep`: the wizard-style explanation shown after an attempt.
- `PracticeAttempt`: a student's answer, estimated auto-mark, and feedback summary.
- `AttemptFeedbackPoint`: per-mark feedback showing likely earned/missed points.
- `GuideArticle`: standalone exam-technique guidance.
- `UserProfile`: role wrapper for Django users: student, teacher, or admin.
- `TeacherStudentAssignment`: links students to the teachers who can view their work.

## User Roles

- Student: can log in, sit past-paper questions, sit generated questions, and read guides.
- Teacher: can do student actions plus view assigned students, attempt history, topic metrics, and generated improvement feedback.
- Admin: teacher permissions plus user creation, role updates, password resets, and teacher-student assignment management.

The implementation uses Django's built-in auth users with an attached `UserProfile`. Admin role users are also marked `is_staff` so they can use Django admin for deeper content management.

## Language

The learner surface is English-only for now. Some Welsh fields still exist in the database from the early scaffold, but model helpers and templates now return English content only. Welsh can be reintroduced later once translations are complete enough to be useful.

## Generated Questions

`exams.services.get_question_generator()` currently returns a deterministic local generator. The boundary is intentionally narrow: topic, marks, difficulty in; prompt, expected answer, and walkthrough steps out.

The local generator is pattern-based. It should generate variations of the recurring WJEC Unit 2 structures:

- HTML tag recall;
- HTML draft-page construction;
- Greenfoot new-world scenario creation;
- Greenfoot identification of superclass/class/object/constructor/act method;
- Greenfoot completion of an existing world with movement, collision, sound, counter, and save-name marks.

An LLM provider can replace `LocalQuestionGenerator` later, with guardrails that:

- retrieve similar past-paper examples,
- require structured JSON output,
- validate mark totals and walkthrough steps,
- store generated questions as drafts for teacher approval.

## PDF Import Pipeline

The attached PDFs should be processed into structured draft questions, not imported directly as display text. Recommended stages:

1. Extract text with PyMuPDF or pdfplumber.
2. Detect question numbers, subparts, marks, and page boundaries.
3. Extract mark-scheme bullet points and match them to question references.
4. Review and edit in the Django admin.
5. Review and publish through the admin.
