from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from exams.models import Paper, Question, SpecificationUnit, Topic, WalkthroughStep
from exams.past_paper_bank import PAPERS, QUESTION_BANK


class Command(BaseCommand):
    help = "Import the structured WJEC Unit 2 past-paper question bank."

    def add_arguments(self, parser):
        parser.add_argument("--replace", action="store_true", help="Replace imported past-paper questions.")

    def handle(self, *args, **options):
        unit, _ = SpecificationUnit.objects.get_or_create(
            code="3500U20-1",
            defaults={
                "title_en": "Unit 2: Computational thinking and programming",
                "title_cy": "Uned 2: Meddwl cyfrifiadurol a rhaglennu",
                "description_en": "WJEC GCSE Computer Science Unit 2 practice.",
                "description_cy": "Ymarfer Uned 2 TGAU Cyfrifiadureg CBAC.",
            },
        )

        if options["replace"]:
            Question.objects.filter(unit=unit, source="past_paper").delete()

        missing_paths = self.missing_resource_paths()
        if missing_paths:
            raise CommandError("Missing past-paper resources:\n" + "\n".join(missing_paths))

        papers = {}
        for paper_data in PAPERS:
            paper, _ = Paper.objects.update_or_create(
                unit=unit,
                series=paper_data["series"],
                code=paper_data["code"],
                defaults={
                    "title": paper_data["title"],
                    "source_pdf_path": paper_data["source_pdf_path"],
                    "mark_scheme_pdf_path": paper_data["mark_scheme_pdf_path"],
                },
            )
            papers[paper.series] = paper

        imported = 0
        for item in QUESTION_BANK:
            paper = papers[item["series"]]
            question, _ = Question.objects.update_or_create(
                unit=unit,
                paper=paper,
                reference=item["reference"],
                defaults={
                    "source": "past_paper",
                    "pattern": item["pattern"],
                    "prompt_en": item["prompt"],
                    "marks": item["marks"],
                    "expected_answer_en": item["answer"],
                    "examiner_note_en": self.examiner_note(item["pattern"]),
                    "difficulty": "standard",
                    "is_published": True,
                },
            )
            question.topics.set([self.topic(unit, name) for name in item["topics"]])
            question.walkthrough_steps.all().delete()
            for index, step in enumerate(self.steps_for(item), start=1):
                WalkthroughStep.objects.create(question=question, order=index, **step)
            imported += 1

        self.stdout.write(self.style.SUCCESS(f"Imported {imported} WJEC Unit 2 questions."))

    def topic(self, unit, name):
        topic, _ = Topic.objects.get_or_create(unit=unit, slug=slugify(name), defaults={"name_en": name})
        return topic

    def missing_resource_paths(self):
        paths = []
        for paper in PAPERS:
            paths.extend([paper["source_pdf_path"], paper["mark_scheme_pdf_path"]])
        return [str(self.resource_path(path)) for path in paths if path and not self.resource_path(path).exists()]

    def resource_path(self, path):
        resource_path = Path(path)
        if not resource_path.is_absolute():
            resource_path = settings.BASE_DIR / resource_path
        return resource_path

    def examiner_note(self, pattern):
        notes = {
            "html_tags": "Mark one tag/effect point at a time. Credit precise tag function and required attributes.",
            "html_draft": "Credit valid HTML that recreates the specified draft. Alternative HTML is acceptable where it works.",
            "greenfoot_create": "Treat each subpart as a checklist mark: world, actor, image, population, movement, save name.",
            "greenfoot_identify": "Use exact Greenfoot vocabulary from the IDE: class, object, superclass, property, method.",
            "greenfoot_complete": "Treat the Greenfoot task as a checklist of population, movement, collision, sound, counter and save-name marks.",
        }
        return notes.get(pattern, "Use the mark scheme as a point-by-point checklist.")

    def steps_for(self, item):
        pattern = item["pattern"]
        if pattern == "html_tags":
            return [
                self.step("Read the tag", "Identify the tag or complete tag shown in the question.", "Write the tag effect in one short phrase.", "The answer comes directly from the tag printed in the question.", "One mark is usually tied to each correct effect or required attribute."),
                self.step("Include content or attributes", "If the tag includes content or attributes, describe their effect too.", item["answer"], "Use the text, href, mailto address or heading content inside the tag.", "2024 splits some marks between the tag effect, parameter and displayed content."),
            ]
        if pattern == "html_draft":
            return [
                self.step("Build the skeleton", "Start with the document structure before visible content.", "<html>\n<head>\n<title>page title from question</title>\n</head>\n<body>\n...\n</body>\n</html>", "The question states the exact page title after the draft.", "html, head, title and body are repeated mark points."),
                self.step("Map draft items to tags", "Turn each visible part of the draft into the matching HTML.", "Use heading tags, <img src=\"file.jpg\">, <p>, <ul>/<li>, and <a href=\"http://...\">link text</a>.", "Read the improved design top to bottom and copy file names/URLs from the question.", "WJEC accepts alternative HTML, not CSS-only answers, when the same formatting is achieved."),
                self.step("Check attributes and save name", "Image and link tags need working attributes, and the final file name matters.", item["answer"], "The image file, URL, page title and save name are all printed below the draft.", "href needs http:// in these mark schemes."),
            ]
        if pattern.startswith("assembly"):
            return [
                self.step("Recall mnemonics", "Match each operation to the exact assembly mnemonic or meaning.", item["answer"], "Use the operation words in each subpart: input, output, store, load, branch, halt, data definition.", "Assembly recall questions are marked one point at a time."),
                self.step("Trace in order", "For trace questions, follow the program line by line and write each OUT value.", "Track register changes after INP, STA, LDA, ADD and SUB; only record values when OUT appears.", "Inputs are given in the question and DAT labels show where values are stored.", "Output order matters."),
            ]
        if pattern in {"algorithm_identify", "algorithm_trace", "algorithm_mixed", "logic_trace"}:
            return [
                self.step("Use the given code/table", "Do not invent new values; trace or identify exactly what is shown.", item["answer"], "The answer is in the given algorithm, truth table or code listing.", "For trace tables, order and cell position matter."),
                self.step("Match vocabulary", "When asked to identify, use the exact variable, line or construct from the question.", "Copy valid identifiers or code fragments exactly where possible.", "Look for local/global variable scope, annotation braces, assignments, loop keywords or logic rows.", "Precise copied evidence earns the mark."),
            ]
        if pattern == "algorithm_write":
            return [
                self.step("List required outputs", "Convert the bullet-point requirements into algorithm steps.", "Prompt, input, process/calculation, output, and selection/loop if required.", "The bullets in the question are the checklist for your answer.", "Each required feature normally maps to one mark."),
                self.step("Write variable-based pseudocode", "Use variables and clear calculations rather than fixed example numbers.", item["answer"], "The example input/output shows behaviour, but your algorithm must work generally.", "Output a variable, not just the sample answer."),
            ]
        if pattern == "greenfoot_create":
            return [
                self.step("Create the world", "Create the named World subclass and set the requested background.", "In Greenfoot, right-click World and create the subclass named in part (a). In that world class constructor, set the background/grid image named in part (a).", "Part (a) gives the world class name and background image. Write/code this in the new World subclass, not in an Actor class.", "One mark for correct world/background."),
                self.step("Create actors and images", "Create the named Actor class or classes and set images.", "Right-click Actor and create each class named in the question. Set each class image to the file named in the same subpart, for example leaf.jpg, sun.jpg, van.jpg or fish.jpg.", "Parts (b), (c) and (d) give class names, images and quantities. Create these in the Actor class tree.", "Class must exist in Greenfoot and use the correct image."),
                self.step("Populate the world constructor", "Add the requested objects so they appear when the world opens.", "Write the population code in the World constructor, for example addObject(new Sun(), 2, 4); and addObject(new Sun(), 6, 4);. Use the number of objects in the question.", "The populate wording tells you object count. Put this inside the World constructor so the examiner sees it on load.", "Population on open is a separate mark."),
                self.step("Add movement and save", "Put random movement in act() where requested and save with the exact name.", "Write movement inside the Actor class act() method, for example move(2); if (Greenfoot.getRandomNumber(100) < 10) { turn(Greenfoot.getRandomNumber(91) - 45); }. Then save using the exact final name.", "Movement wording and save name are in the final subparts. act() belongs in the Actor class that should move.", "Random movement and save name are recurring easy marks."),
            ]
        if pattern == "greenfoot_identify":
            return [
                self.step("Inspect the IDE", "Use the class diagram/source code, not memory.", item["answer"], "Classes are shown in the Greenfoot class list; objects are in the world; properties and methods are in source code.", "Use exact names and capitalisation where possible."),
                self.step("Separate terms", "Superclass, class, property, method and parameter are different things.", "World/Actor are superclasses; act() is the repeated method; private fields are properties.", "The subpart wording tells you which kind of item to look for.", "Do not give an object name where a class is requested."),
            ]
        if pattern == "greenfoot_complete":
            return [
                self.step("Populate the world", "Add the exact objects and quantities so they appear when the world opens.", "Write addObject(...) calls in the World constructor. Add one player object, then add the required collectibles/hazards using the exact class names and quantities from part (a).", "Part (a) lists object names and quantities. This code belongs in the World class constructor.", "Usually three marks are available just for population."),
                self.step("Code random movement", "Random movement belongs to the non-player objects named in part (b).", "In each non-player Actor class act() method, write move(...); plus random turning such as if (Greenfoot.getRandomNumber(100) < 10) { turn(Greenfoot.getRandomNumber(91) - 45); }.", "Part (b) names the classes that should turn and move randomly. Do not put this in the player class unless asked.", "Random movement is a distinct mark."),
                self.step("Code player movement", "Arrow-key movement belongs in the player Actor class.", "In the player act() method, write key checks such as if (Greenfoot.isKeyDown(\"left\")) { turn(-4); } and if (Greenfoot.isKeyDown(\"up\")) { move(4); }. Use a speed that is sensible compared with other objects.", "Part (c) names the player class and says it moves with arrow keys.", "Arrow-key movement and appropriate speed can be separate marks."),
                self.step("Code collision removal", "The story word tells you which object disappears.", "In the player or relevant colliding class, write Actor item = getOneIntersectingObject(Item.class); if (item != null) { getWorld().removeObject(item); }. Replace Item with the class named in the question.", "Part (d) says collects/eats/drinks/catches and names the object removed.", "Removal on collision is a separate mark."),
                self.step("Code sound and counter", "Handle each score/sound instruction as a separate checklist item.", "Where the collision is handled, add Greenfoot.playSound(\"sound.wav\");. Add a Counter object to the world. Call a counter method with +1 or a negative amount when the question says gains or loses points.", "Parts (e), (f) and (g) describe sound, counter, increment/decrement and parameter passing.", "These are individual mark-scheme bullets."),
                self.step("Save exactly", "Save the completed Greenfoot world using the required final name.", "Copy the final save name exactly from the last subpart.", "Part (h) gives the saved world name.", "Capitalisation is often ignored, but spelling should be right."),
            ]
        return [self.step("Use the mark scheme", "Work through the mark points one by one.", item["answer"], "The question wording and mark scheme bullets are the source.", "Each bullet is a likely mark.")]

    def step(self, title, body, write_this, source_hint, mark_focus):
        return {
            "title_en": title,
            "body_en": body,
            "write_this_en": write_this,
            "source_hint_en": source_hint,
            "mark_focus_en": mark_focus,
        }
