from dataclasses import dataclass
import re


STOP_WORDS = {
    "the", "and", "for", "with", "this", "that", "from", "into", "when", "where", "which",
    "should", "would", "could", "then", "than", "they", "them", "your", "each", "mark",
    "marks", "question", "answer", "write", "using", "required", "correct", "example",
}


@dataclass
class GeneratedQuestionDraft:
    prompt_en: str
    expected_answer_en: str
    walkthrough_steps: list[dict]
    topic_name: str
    marks: int
    difficulty: str


class LocalQuestionGenerator:
    """Deterministic fallback until an LLM provider is connected."""

    def generate(self, pattern, topic, marks, difficulty):
        topic_name = topic.strip() or self.default_topic(pattern)
        templates = {
            "html_tags": self.html_tags,
            "html_draft": self.html_draft,
            "greenfoot_create": self.greenfoot_create,
            "greenfoot_complete": self.greenfoot_complete,
            "greenfoot_identify": self.greenfoot_identify,
        }
        prompt, answer, steps = templates.get(pattern, self.html_tags)(topic_name, marks)
        return GeneratedQuestionDraft(
            prompt_en=prompt,
            expected_answer_en=answer,
            walkthrough_steps=steps,
            topic_name=self.topic_label(pattern),
            marks=marks,
            difficulty=difficulty,
        )

    def default_topic(self, pattern):
        return {
            "html_tags": "HTML formatting",
            "html_draft": "school club web page",
            "greenfoot_create": "advert scenario",
            "greenfoot_complete": "collecting game",
            "greenfoot_identify": "Greenfoot class diagram",
        }.get(pattern, "Unit 2")

    def topic_label(self, pattern):
        return "HTML" if pattern.startswith("html") else "Greenfoot"

    def html_tags(self, topic, marks):
        prompt = (
            "State the HTML tags needed to create common page elements. "
            "Include tags for a main heading, a paragraph, a line break, an image, and a hyperlink."
        )
        answer = "Award credit for valid opening/closing tags or accepted single tags, for example <h1>, <p>, <br>, <img src=\"...\">, and <a href=\"...\">.</a>"
        return prompt, answer, [
            {
                "title": "Read for exact tag use",
                "body": "These WJEC questions normally award one mark per correct tag or tag pair.",
                "write_this": "`<h1>` creates a main heading; `<p>` creates a paragraph; `<br>` creates a line break; `<img src=\"image.jpg\">` displays an image; `<a href=\"page.html\">Link text</a>` creates a hyperlink.",
                "source_hint": "Get each answer from the wording after 'State the HTML tags needed to...' and match each requested page element to the tag used to create it.",
                "mark_focus": "Do not describe the tag when the question asks you to state/write it.",
            },
            {
                "title": "Include attributes where needed",
                "body": "Image and hyperlink tags usually need `src` or `href` to be meaningful.",
                "write_this": "For images write `src` for the file name. For links write `href` for the target page.",
                "source_hint": "If the question gives a file name such as pets.jpg or a second page name, copy that into the correct attribute.",
                "mark_focus": "A correct attribute can be the difference between a vague and creditworthy answer.",
            },
        ]

    def html_draft(self, topic, marks):
        prompt = (
            f"A draft design for an HTML web page about {topic} is shown to a student. "
            "Write the HTML that would display a title, a heading, an image, two short paragraphs, and a hyperlink to another page."
        )
        answer = "A strong response uses a valid HTML structure with <html>, <head>, <title>, <body>, heading tags, paragraph tags, an <img> tag with src/alt, and an <a href> hyperlink."
        return prompt, answer, [
            {
                "title": "Build the skeleton first",
                "body": "Start with html, head/title, and body before adding visible content.",
                "write_this": "<html>\n<head>\n<title>Page title from the draft</title>\n</head>\n<body>\n...\n</body>\n</html>",
                "source_hint": "Take the page title from the top/window title part of the draft, not from the large visible heading.",
                "mark_focus": "The mark schemes repeatedly credit the page structure.",
            },
            {
                "title": "Match the draft",
                "body": "Use heading, paragraph, image, and hyperlink tags for the matching parts of the design.",
                "write_this": "<h1>Visible heading</h1>\n<img src=\"given-file.jpg\" alt=\"brief description\">\n<p>First paragraph text</p>\n<p>Second paragraph text</p>\n<a href=\"given-page.html\">Link text</a>",
                "source_hint": "Read the draft layout from top to bottom and turn each visible item into the matching HTML tag.",
                "mark_focus": "The answer must produce the shown formatting/content, not just any valid page.",
            },
            {
                "title": "Avoid CSS-only answers",
                "body": "These papers usually expect HTML tag solutions unless the question asks for CSS.",
                "write_this": "Use HTML tags such as `<h1>`, `<p>`, `<img>` and `<a>` rather than CSS rules.",
                "source_hint": "The mark scheme wording accepts alternative HTML solutions, so stay in HTML unless CSS is explicitly named.",
                "mark_focus": "Alternative HTML is accepted when it works.",
            },
        ]

    def greenfoot_create(self, topic, marks):
        prompt = (
            f"A company wants a new Greenfoot scenario for a {topic}. "
            "Create a new World class with a 9 x 9 grid background, create one Actor subclass with a suitable image, add two instances when the world opens, make them move randomly, and save the world with a suitable final name."
        )
        answer = "Credit is for a new World subclass, correct background, Actor subclass with image, pre-populated actors, random movement in the actor act method, and correct saved world name."
        return prompt, answer, [
            {
                "title": "World first",
                "body": "Create the World subclass and set the background/grid before populating it.",
                "write_this": "Create a World subclass with the exact name in the question, for example `Advert`, and set its background to the named 9 x 9 grid image.",
                "source_hint": "The class name and background image come directly from part (a) of the Greenfoot question.",
                "mark_focus": "One mark is usually tied to the new world class/background.",
            },
            {
                "title": "Actor class and image",
                "body": "Create the Actor subclass and assign the requested image.",
                "write_this": "Create the named Actor subclass, for example `Van`, `Sun`, `Leaf` or `Fish`, and set its image to the file named in the question.",
                "source_hint": "Look at part (b): it normally gives both the actor class name and image file.",
                "mark_focus": "The class must exist in Greenfoot and use the correct image.",
            },
            {
                "title": "Populate on open",
                "body": "Add objects in the world constructor so they appear when the scenario opens.",
                "write_this": "In the World constructor, add the required number of objects, e.g. `addObject(new Van(), x, y);` twice.",
                "source_hint": "The number of objects comes from the populate instruction, usually part (c).",
                "mark_focus": "Manual placement without saving the populated world is risky.",
            },
            {
                "title": "Random movement",
                "body": "Use movement and random turning in the actor's act method.",
                "write_this": "In the Actor `act()` method, use movement plus random turning, e.g. `move(2); if (Greenfoot.getRandomNumber(100) < 10) { turn(Greenfoot.getRandomNumber(91) - 45); }`.",
                "source_hint": "This comes from the phrase 'turn and move randomly' in the Greenfoot task.",
                "mark_focus": "The mark scheme looks for random movement when the world runs.",
            },
        ]

    def greenfoot_complete(self, topic, marks):
        prompt = (
            f"Open an existing Greenfoot world for a {topic} game. "
            "Populate the world with one player object and several collectible/hazard objects. "
            "Make non-player objects move randomly, move the player with the arrow keys, remove a collectible on collision, play a sound on collision, add a counter, and save the completed world."
        )
        answer = "Credit is for pre-population, random movement for objects, arrow-key movement for the player, collision removal, sound, counter, and saving with the required final name."
        return prompt, answer, [
            {
                "title": "Populate the world",
                "body": "Add the specified objects so they are present when the world loads.",
                "write_this": "Add one player object and the required number of collectible/hazard objects in the world constructor.",
                "source_hint": "Use the object names and quantities from part (a) of the existing-world question.",
                "mark_focus": "The first marks are often for correct starting objects.",
            },
            {
                "title": "Separate movement behaviours",
                "body": "Random movement belongs to objects such as hazards or collectibles; arrow-key movement belongs to the player.",
                "write_this": "For non-player objects: `move(...)` and random `turn(...)`. For the player: check `Greenfoot.isKeyDown(\"left\")`, `\"right\"`, `\"up\"`, and `\"down\"`.",
                "source_hint": "Parts (b) and (c) split the movement requirements between object classes and the player class.",
                "mark_focus": "Mixing these behaviours loses easy marks.",
            },
            {
                "title": "Use collision methods",
                "body": "Check for intersecting objects, then remove or respond to the object in the world.",
                "write_this": "In the player class, get the collided object, then remove it: `Actor item = getOneIntersectingObject(Item.class); if (item != null) { getWorld().removeObject(item); }`.",
                "source_hint": "This answer comes from the instruction that the player collects/eats/removes an object on collision.",
                "mark_focus": "Collision handling is a recurring Greenfoot mark point.",
            },
            {
                "title": "Add polish items",
                "body": "Sound, counter, and final saved name are small but repeatable marks.",
                "write_this": "Add `Greenfoot.playSound(\"sound.wav\");`, update the counter, and save the world using the exact final name in the question.",
                "source_hint": "These usually appear as later subparts: sound, counter, then final save instruction.",
                "mark_focus": "Do not leave them until the end of the exam.",
            },
        ]

    def greenfoot_identify(self, topic, marks):
        prompt = "In a Greenfoot world, identify one superclass, one class, one object, one constructor, and the method that runs automatically in each frame."
        answer = "Typical correct answers include World or Actor as superclasses, named subclasses as classes, placed instances as objects, a class-name constructor, and act() as the automatically repeated method."
        return prompt, answer, [
            {
                "title": "Class versus object",
                "body": "The class is the blueprint shown in the class list; the object is an instance placed in the world.",
                "write_this": "Write the class name from the class list for 'class'. Write a placed instance in the world for 'object'.",
                "source_hint": "Use the Greenfoot IDE: classes are on the right; objects are visible in the world.",
                "mark_focus": "This distinction is tested frequently.",
            },
            {
                "title": "Superclass clue",
                "body": "Greenfoot classes commonly inherit from World or Actor.",
                "write_this": "Write `World` or `Actor` when the question asks for a superclass, if the shown class inherits from it.",
                "source_hint": "Look at the inheritance arrow/extends relationship in the class diagram or source code.",
                "mark_focus": "World and Actor are commonly accepted superclass answers.",
            },
            {
                "title": "Automatic method",
                "body": "The act method runs repeatedly while the scenario is running.",
                "write_this": "Write `act()` for the method that is automatically run in each frame.",
                "source_hint": "Find the method comment or method header inside an Actor class.",
                "mark_focus": "Use the exact method name where possible.",
            },
        ]


def get_question_generator():
    return LocalQuestionGenerator()


def normalize_text(value):
    return re.sub(r"\s+", " ", value.lower()).strip()


def answer_contains(answer_text, candidate):
    answer = normalize_text(answer_text)
    candidate = candidate.strip().lower()
    if not candidate:
        return False
    if candidate.startswith("<") and candidate in answer_text.lower():
        return True
    if re.match(r"^[a-z]{2,5}$", candidate) and candidate.upper() in {"INP", "OUT", "STA", "LDA", "ADD", "SUB", "BRA", "HLT", "DAT"}:
        return candidate.lower() in answer
    return normalize_text(candidate) in answer


def keywords_from(text):
    raw = re.findall(r"[A-Za-z][A-Za-z0-9_]*|<[^>\s]+|https?://[^\s\">]+|www\.[^\s\">]+", text)
    keywords = []
    for token in raw:
        cleaned = token.strip(".,;:()[]{}\"'`")
        if len(cleaned) < 3 and not cleaned.startswith("<"):
            continue
        if cleaned.lower() in STOP_WORDS:
            continue
        if cleaned not in keywords:
            keywords.append(cleaned)
    return keywords[:14]


def build_mark_criteria(question):
    steps = list(question.walkthrough_steps.all())
    answer_criteria = []
    for chunk in re.split(r";|\.\s+", question.expected_answer_en):
        chunk = chunk.strip()
        if chunk:
            answer_criteria.append(
                {
                    "label": chunk[:120],
                    "source_hint": "Use this mark-scheme point from the expected answer.",
                    "improvement": chunk,
                    "keywords": keywords_from(chunk),
                }
            )

    criteria = []
    if steps:
        for step in steps:
            source = "\n".join([step.write_this_en, step.mark_focus_en, step.title_en])
            criteria.append(
                {
                    "label": step.title_en,
                    "source_hint": step.source_hint_en,
                    "improvement": step.write_this_en or step.body_en,
                    "keywords": keywords_from(source),
                }
            )

    if len(answer_criteria) > len(criteria) or question.marks > len(criteria):
        criteria = answer_criteria

    if not criteria:
        criteria.append(
            {
                "label": "Relevant answer",
                "source_hint": "Use the question wording and mark scheme.",
                "improvement": question.expected_answer_en,
                "keywords": keywords_from(question.expected_answer_en),
            }
        )
    return criteria[: max(question.marks, 1)]


def auto_mark_attempt(attempt):
    from .models import AttemptFeedbackPoint

    question = attempt.question
    criteria = build_mark_criteria(question)
    AttemptFeedbackPoint.objects.filter(attempt=attempt).delete()

    awarded = 0
    for index, criterion in enumerate(criteria, start=1):
        matched_terms = [term for term in criterion["keywords"] if answer_contains(attempt.answer_text, term)]
        threshold = 1 if len(criterion["keywords"]) <= 2 else min(2, len(criterion["keywords"]))
        is_awarded = len(matched_terms) >= threshold
        if is_awarded:
            awarded += 1
        AttemptFeedbackPoint.objects.create(
            attempt=attempt,
            order=index,
            label=criterion["label"],
            awarded=is_awarded,
            marks=1,
            evidence=", ".join(matched_terms[:6]) if matched_terms else "",
            improvement=criterion["improvement"],
            source_hint=criterion["source_hint"],
        )

    awarded = min(awarded, question.marks)
    total_points = max(len(criteria), 1)
    scaled_award = round((awarded / total_points) * question.marks)
    scaled_award = min(scaled_award, question.marks)
    missed = question.marks - scaled_award
    attempt.auto_awarded_marks = scaled_award
    attempt.self_assessed_marks = scaled_award
    attempt.auto_feedback_summary = (
        f"Estimated {scaled_award}/{question.marks}. "
        f"You appear to have covered {awarded} of {total_points} mark points. "
        f"Review the {missed} missed mark point{'s' if missed != 1 else ''} below."
    )
    attempt.save(update_fields=["auto_awarded_marks", "self_assessed_marks", "auto_feedback_summary", "updated_at"])
    return attempt


def generate_student_feedback(student, attempts):
    total = attempts.count()
    if total == 0:
        return "No attempts yet. Start with a short mix of past-paper and generated questions, then review walkthroughs after each answer."

    weak_attempts = []
    topic_counts = {}
    for attempt in attempts.select_related("question").prefetch_related("question__topics"):
        if attempt.question.marks and attempt.auto_awarded_marks < attempt.question.marks:
            weak_attempts.append(attempt)
        for topic in attempt.question.topics.all():
            topic_counts[topic.name_en] = topic_counts.get(topic.name_en, 0) + 1

    attempted_topics = ", ".join(sorted(topic_counts)) or "general Unit 2 skills"
    if not weak_attempts:
        return f"{student.get_full_name() or student.username} is covering the detected mark points well. Next step: add stretch questions and ask for more precise exam vocabulary."

    common_gap = weak_attempts[0].question.examiner_note_en or "Use precise computing vocabulary and apply each point to the scenario."
    return (
        f"Focus revision on {attempted_topics}. The student should compare their answers with the walkthrough, "
        f"then rewrite one improved answer after each attempt. Priority feedback: {common_gap}"
    )
