from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand

from exams.models import GuideArticle, Paper, Question, SpecificationUnit, TeacherStudentAssignment, Topic, UserProfile, WalkthroughStep


class Command(BaseCommand):
    help = "Seed a small Unit 2 practice dataset."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete demo questions and guides before seeding.")

    def handle(self, *args, **options):
        if options["reset"]:
            WalkthroughStep.objects.all().delete()
            Question.objects.all().delete()
            GuideArticle.objects.all().delete()
            Paper.objects.all().delete()
            Topic.objects.all().delete()
            SpecificationUnit.objects.filter(code="3500U20-1").delete()
        else:
            Question.objects.filter(reference__startswith="Demo ").delete()
            Question.objects.filter(reference="S24 Q3").delete()

        unit, _ = SpecificationUnit.objects.get_or_create(
            code="3500U20-1",
            defaults={
                "title_en": "Unit 2: Computational thinking and programming",
                "title_cy": "Uned 2: Meddwl cyfrifiadurol a rhaglennu",
                "description_en": "WJEC GCSE Computer Science Unit 2 practice.",
                "description_cy": "Ymarfer Uned 2 TGAU Cyfrifiadureg CBAC.",
            },
        )

        paper, _ = Paper.objects.get_or_create(
            unit=unit,
            series="Summer 2024",
            code="3500U20-1",
            defaults={
                "title": "GCSE Computer Science Unit 2",
                "source_pdf_path": "source_materials/wjec-unit2/S24-3500U20-1.pdf",
                "mark_scheme_pdf_path": "source_materials/wjec-unit2/S24-3500U20-1-ms.pdf",
            },
        )

        topics = {}
        for name_en, name_cy in [
            ("HTML", "HTML"),
            ("Greenfoot", "Greenfoot"),
            ("Greenfoot world setup", "Gosod byd Greenfoot"),
            ("Greenfoot collision and scoring", "Gwrthdrawiad a sgorio Greenfoot"),
        ]:
            topic, _ = Topic.objects.get_or_create(unit=unit, name_en=name_en, defaults={"name_cy": name_cy})
            topics[name_en] = topic
        Topic.objects.filter(
            unit=unit,
            name_en__in=["Algorithms", "Programming constructs", "Validation and testing", "Databases"],
        ).delete()

        samples = [
            {
                "reference": "S24 Q1",
                "topics": ["HTML"],
                "marks": 5,
                "prompt_en": "State the effect of five HTML tags commonly used in WJEC Unit 2 web-page questions: <html>, <head>, <title>, <body>, and <a>.",
                "prompt_cy": "Nodwch effaith pum tag HTML a ddefnyddir yn aml yng nghwestiynau tudalen we Uned 2 CBAC: <html>, <head>, <title>, <body>, ac <a>.",
                "expected_answer_en": "<html> defines the HTML document, <head> contains metadata/title information, <title> sets the browser/tab title, <body> contains visible page content, and <a> creates a hyperlink when used with href.",
                "expected_answer_cy": "Mae <html> yn diffinio'r ddogfen HTML, mae <head> yn cynnwys metadata/gwybodaeth teitl, mae <title> yn gosod teitl y porwr/tab, mae <body> yn cynnwys cynnwys gweladwy'r dudalen, ac mae <a> yn creu hyperddolen pan gaiff ei ddefnyddio gyda href.",
                "steps": [
                    ("Match one tag to one effect", "These opening Unit 2 questions are usually direct recall: tag on one side, effect on the other.", "Expect one mark for each correct effect."),
                    ("Use precise wording", "Say what the tag does in the page structure rather than giving a vague phrase such as 'makes a website'.", "Precision earns the mark quickly."),
                    ("Remember attributes", "For hyperlink/image tags, mention href or src when the effect depends on an attribute.", "Attributes often make an answer complete."),
                ],
            },
            {
                "reference": "S24 Q2",
                "topics": ["HTML"],
                "marks": 10,
                "prompt_en": "A draft web page for a local event contains a page title, a large heading, an image, two paragraphs and a link to a second page. Write the HTML tags needed to create the structure and content shown in the draft.",
                "prompt_cy": "Mae tudalen we ddrafft ar gyfer digwyddiad lleol yn cynnwys teitl tudalen, pennawd mawr, delwedd, dau baragraff a dolen i ail dudalen. Ysgrifennwch y tagiau HTML sydd eu hangen i greu'r strwythur a'r cynnwys a ddangosir yn y drafft.",
                "expected_answer_en": "A valid answer should use an HTML document structure and suitable tags such as <html>, <head>, <title>, <body>, <h1>, <img src=\"...\" alt=\"...\">, <p>, and <a href=\"...\">. Alternative HTML tag choices can earn credit where they produce the requested draft.",
                "expected_answer_cy": "Dylai ateb dilys ddefnyddio strwythur dogfen HTML a thagiau addas megis <html>, <head>, <title>, <body>, <h1>, <img src=\"...\" alt=\"...\">, <p>, ac <a href=\"...\">. Gellir rhoi credyd am ddewisiadau HTML amgen pan fyddant yn cynhyrchu'r drafft gofynnol.",
                "steps": [
                    ("Start with document structure", "Put the title in the head and the visible content in the body.", "The mark schemes repeatedly credit valid HTML structure."),
                    ("Map each draft item to a tag", "Heading, image, paragraphs and hyperlink each need their own appropriate tags.", "Work through the draft systematically."),
                    ("Use working attributes", "Images need src, links need href, and alt text is good practice.", "Alternative HTML is accepted when it works."),
                ],
            },
            {
                "reference": "S24 Q6 pattern",
                "topics": ["Greenfoot", "Greenfoot world setup"],
                "marks": 5,
                "prompt_en": "A business would like a new Greenfoot advert scenario. Create a new World class called Advert with a 9 x 9 grid background, create an Actor subclass with the requested image, populate the world with two instances, make them move randomly, and save the world using the required final name.",
                "prompt_cy": "Hoffai busnes senario hysbyseb Greenfoot newydd. Crëwch ddosbarth World newydd o'r enw Advert gyda chefndir grid 9 x 9, crëwch is-ddosbarth Actor gyda'r ddelwedd ofynnol, poblogwch y byd gyda dau wrthrych, gwnewch iddynt symud ar hap, ac arbedwch y byd gyda'r enw terfynol gofynnol.",
                "expected_answer_en": "Credit is for the new World class/background, correct Actor subclass and image, two instances present when the world opens, random movement code in the actor class, and saving the world with the required final name.",
                "expected_answer_cy": "Rhoddir credyd am y dosbarth World/cefndir newydd, yr is-ddosbarth Actor a'r ddelwedd gywir, dau wrthrych yn bresennol pan fydd y byd yn agor, cod symud ar hap yn y dosbarth actor, ac arbed y byd gyda'r enw terfynol gofynnol.",
                "steps": [
                    ("Create the World class", "The world class and background are separate mark points.", "Use the exact class/background requested."),
                    ("Create and image the Actor", "The Actor subclass must exist and have the requested image.", "The class list on the right is part of the evidence."),
                    ("Populate in the constructor", "Add two objects so the world is populated when it opens.", "This is more reliable than only dragging objects manually."),
                    ("Add random movement", "Use move plus a random turn in the actor's act method.", "Random movement is a recurring WJEC Greenfoot mark."),
                    ("Save with the final name", "The final saved world name is a small but repeated mark.", "Do not lose the final administrative mark."),
                ],
            },
            {
                "reference": "S24 Q7 pattern",
                "topics": ["Greenfoot", "Greenfoot collision and scoring"],
                "marks": 13,
                "prompt_en": "Open an existing Greenfoot world. Populate it with one player object and several moving objects, make the non-player objects move randomly, move the player with the arrow keys, remove a collectible on collision, play a sound on collision, add a counter, and save the completed world.",
                "prompt_cy": "Agorwch fyd Greenfoot presennol. Poblogwch ef gydag un gwrthrych chwaraewr a sawl gwrthrych symudol, gwnewch i'r gwrthrychau nad ydynt yn chwaraewyr symud ar hap, symudwch y chwaraewr gyda'r bysellau saeth, tynnwch gasgladwy ar wrthdrawiad, chwaraewch sain ar wrthdrawiad, ychwanegwch gownter, ac arbedwch y byd gorffenedig.",
                "expected_answer_en": "Credit is for correct pre-population, random movement for non-player objects, arrow-key player movement, collision detection and removal, sound on collision, a counter added to the world, and the correct saved final world.",
                "expected_answer_cy": "Rhoddir credyd am boblogi cywir, symud ar hap ar gyfer gwrthrychau nad ydynt yn chwaraewyr, symudiad chwaraewr gyda'r saethau, canfod gwrthdrawiad a thynnu gwrthrych, sain ar wrthdrawiad, cownter wedi'i ychwanegu at y byd, ac arbed y byd terfynol cywir.",
                "steps": [
                    ("Populate before coding", "Make sure the required player and other objects are in the world on load.", "The first mark often checks the opening state."),
                    ("Separate random and player movement", "Objects such as hazards or collectibles turn and move randomly; the player responds to arrow keys.", "Do not put arrow-key code in every class."),
                    ("Handle collisions", "Use Greenfoot collision checks to detect the object and remove it from the world.", "Collision removal is a regular mark point."),
                    ("Add sound and counter", "These are often single marks but easy to miss.", "Treat them as checklist items."),
                    ("Save exactly as requested", "The final file/world name matters.", "A correct save name can earn the final mark."),
                ],
            },
        ]

        for sample in samples:
            question, created = Question.objects.update_or_create(
                unit=unit,
                paper=paper,
                reference=sample["reference"],
                defaults={
                    "prompt_en": sample["prompt_en"],
                    "prompt_cy": sample["prompt_cy"],
                    "marks": sample["marks"],
                    "expected_answer_en": sample["expected_answer_en"],
                    "expected_answer_cy": sample["expected_answer_cy"],
                    "examiner_note_en": "Use precise GCSE computing vocabulary and apply it to the scenario.",
                },
            )
            question.topics.set([topics[name] for name in sample["topics"]])
            question.walkthrough_steps.all().delete()
            for index, (title, body, focus) in enumerate(sample["steps"], start=1):
                write_this, source_hint = self.step_details(title)
                WalkthroughStep.objects.create(
                    question=question,
                    order=index,
                    title_en=title,
                    body_en=body,
                    mark_focus_en=focus,
                    write_this_en=write_this,
                    source_hint_en=source_hint,
                )

        GuideArticle.objects.get_or_create(
            unit=unit,
            slug="command-words",
            defaults={
                "title_en": "How to handle command words",
                "title_cy": "Sut i ymdrin â geiriau gorchymyn",
                "summary_en": "Turn command words into a marking strategy before you start writing.",
                "summary_cy": "Trowch eiriau gorchymyn yn strategaeth farcio cyn dechrau ysgrifennu.",
                "body_en": "State means give a short answer.\n\nDescribe means give a point and add detail about what it does.\n\nExplain means connect the point to a reason, result, or benefit.\n\nCompare means write about both items and make the difference clear.",
                "body_cy": "Mae nodwch yn golygu rhoi ateb byr.\n\nMae disgrifiwch yn golygu rhoi pwynt ac ychwanegu manylion am yr hyn mae'n ei wneud.\n\nMae esboniwch yn golygu cysylltu'r pwynt â rheswm, canlyniad neu fantais.\n\nMae cymharwch yn golygu ysgrifennu am y ddau beth a gwneud y gwahaniaeth yn glir.",
                "order": 1,
            },
        )
        GuideArticle.objects.get_or_create(
            unit=unit,
            slug="answering-mark-questions",
            defaults={
                "title_en": "Writing answers that earn marks",
                "title_cy": "Ysgrifennu atebion sy'n ennill marciau",
                "summary_en": "Use marks as a clue for how many separate points the examiner expects.",
                "summary_cy": "Defnyddiwch farciau fel cliw i nifer y pwyntiau ar wahân mae'r arholwr yn eu disgwyl.",
                "body_en": "For a two-mark answer, expect one clear point and one explanation, or two separate stated points.\n\nFor four or more marks, plan the answer as short mark-sized chunks. Use the scenario in each chunk where possible.\n\nAfter writing, check that every sentence either names a computing idea, explains it, or applies it to the scenario.",
                "body_cy": "Ar gyfer ateb dau farc, disgwyliwch un pwynt clir ac un esboniad, neu ddau bwynt ar wahân.\n\nAr gyfer pedwar marc neu fwy, cynlluniwch yr ateb fel darnau byr sy'n werth marc. Defnyddiwch y senario ym mhob darn lle bo'n bosibl.\n\nAr ôl ysgrifennu, gwiriwch fod pob brawddeg naill ai'n enwi syniad cyfrifiadura, yn ei esbonio, neu'n ei gymhwyso i'r senario.",
                "order": 2,
            },
        )
        GuideArticle.objects.update_or_create(
            unit=unit,
            slug="wjec-html-questions",
            defaults={
                "title_en": "WJEC Unit 2 HTML question pattern",
                "title_cy": "Patrwm cwestiynau HTML Uned 2 CBAC",
                "summary_en": "How to approach tag recall and draft web-page HTML questions.",
                "summary_cy": "Sut i fynd ati i ateb cwestiynau tagiau HTML a thudalennau gwe drafft.",
                "body_en": "The HTML section normally starts with direct tag knowledge, then asks you to write or insert HTML to match a draft page.\n\nFor tag questions, give the exact tag and its effect. For page questions, build the skeleton first: html, head, title and body. Then map each visible item in the draft to a tag: heading, image, paragraph, list or hyperlink.\n\nRemember that image and hyperlink tags need attributes such as src and href. WJEC mark schemes often accept alternative HTML if it produces the required result, but CSS-only answers are not the target unless CSS is requested.",
                "body_cy": "Mae'r adran HTML fel arfer yn dechrau gyda gwybodaeth uniongyrchol am dagiau, ac yna'n gofyn i chi ysgrifennu neu fewnosod HTML i gyd-fynd â thudalen ddrafft.\n\nAr gyfer cwestiynau tagiau, rhowch y tag union a'i effaith. Ar gyfer cwestiynau tudalen, adeiladwch y sgerbwd yn gyntaf: html, head, title a body. Yna cysylltwch bob eitem weladwy yn y drafft â thag: pennawd, delwedd, paragraff, rhestr neu hyperddolen.\n\nCofiwch fod angen priodoleddau megis src a href ar dagiau delwedd a hyperddolen. Mae cynlluniau marcio CBAC yn aml yn derbyn HTML amgen os yw'n cynhyrchu'r canlyniad gofynnol, ond nid atebion CSS yn unig yw'r targed oni bai bod CSS wedi'i ofyn amdano.",
                "order": 3,
            },
        )
        GuideArticle.objects.update_or_create(
            unit=unit,
            slug="wjec-greenfoot-questions",
            defaults={
                "title_en": "WJEC Unit 2 Greenfoot question pattern",
                "title_cy": "Patrwm cwestiynau Greenfoot Uned 2 CBAC",
                "summary_en": "The repeated Greenfoot checklist: world, actors, movement, collision, counter, save name.",
                "summary_cy": "Rhestr wirio Greenfoot sy'n ailadrodd: byd, actorion, symud, gwrthdrawiad, cownter, enw cadw.",
                "body_en": "The Greenfoot practical questions are checklist-heavy. For a new scenario, expect marks for the World class, background, Actor subclass, image, objects appearing when the world opens, random movement, and the final saved name.\n\nFor an existing world, expect marks for pre-populating objects, random movement for non-player objects, arrow-key movement for the player, collision detection, removing an object, playing a sound, adding/updating a counter, and saving with the exact requested final name.\n\nFor identification questions, keep the vocabulary tight: World or Actor can be a superclass, a class is the blueprint in the class list, an object is an instance in the world, a constructor has the class name, and act() runs automatically while the scenario runs.",
                "body_cy": "Mae cwestiynau ymarferol Greenfoot yn seiliedig ar restr wirio. Ar gyfer senario newydd, disgwyliwch farciau am y dosbarth World, cefndir, is-ddosbarth Actor, delwedd, gwrthrychau sy'n ymddangos pan fydd y byd yn agor, symud ar hap, ac enw cadw terfynol.\n\nAr gyfer byd presennol, disgwyliwch farciau am boblogi gwrthrychau, symud ar hap ar gyfer gwrthrychau nad ydynt yn chwaraewyr, symud y chwaraewr gyda bysellau saeth, canfod gwrthdrawiad, tynnu gwrthrych, chwarae sain, ychwanegu/diweddaru cownter, ac arbed gyda'r union enw terfynol.\n\nAr gyfer cwestiynau adnabod, cadwch yr eirfa'n dynn: gall World neu Actor fod yn uwchddosbarth, dosbarth yw'r glasbrint yn y rhestr dosbarthiadau, gwrthrych yw enghraifft yn y byd, mae adeiladydd yn defnyddio enw'r dosbarth, ac mae act() yn rhedeg yn awtomatig tra bo'r senario'n rhedeg.",
                "order": 4,
            },
        )
        GuideArticle.objects.update_or_create(
            unit=unit,
            slug="greenfoot-story-language",
            defaults={
                "title_en": "Greenfoot story language",
                "summary_en": "Translate exam wording such as collects, eats, drinks and catches into code actions.",
                "body_en": "WJEC Greenfoot questions often describe code using story language.\n\nCollects, eats or drinks usually means: detect a collision, remove the object, play a sound if requested, and update a counter.\n\nCatches the player usually means: detect a collision with the player object and remove the player from the world.\n\nGains or loses points means: call the counter method with a positive or negative value. If the mark scheme mentions parameter passing, avoid making a separate new method for every score change. Use one method that accepts an amount.\n\nWhen answering or coding, underline the story verb first. Then write the exact Greenfoot action next to it.",
                "order": 5,
            },
        )
        GuideArticle.objects.update_or_create(
            unit=unit,
            slug="model-answer-builder",
            defaults={
                "title_en": "Building a model answer",
                "summary_en": "Use the question, resources and mark scheme as a line-by-line answer plan.",
                "body_en": "A model answer is not one long paragraph. It is a set of mark-sized pieces.\n\nStep 1: copy the named item from the question. For HTML this might be a file name, URL or page title. For Greenfoot it might be a world name, actor class, object count or save name.\n\nStep 2: write the syntax that uses that item. For HTML, that means tags and attributes. For Greenfoot, that means constructor code, act methods, collision checks, sound calls and counter updates.\n\nStep 3: check the mark scheme pattern. If the paper asks for 13 marks, expect separate marks for population, movement, collision, sound, counter, score change and save name.\n\nStep 4: compare your answer with the walkthrough. Anything in the model answer builder that is missing from your answer is a revision target.",
                "order": 6,
            },
        )

        call_command("import_past_papers")
        self.create_demo_users()
        self.stdout.write(self.style.SUCCESS("Seeded demo Unit 2 VLE content."))

    def step_details(self, title):
        details = {
            "Match one tag to one effect": (
                "<html> defines the document. <head> contains metadata. <title> sets the browser tab title. <body> contains visible page content. <a href=\"page.html\">text</a> creates a hyperlink.",
                "Use the list of tags printed in the question. Each tag normally maps to one mark-scheme bullet.",
            ),
            "Use precise wording": (
                "Write short effect statements such as '<body> contains the content displayed on the web page.'",
                "The mark scheme rewards the effect of the tag, not a general description of websites.",
            ),
            "Remember attributes": (
                "For a link, write href with the target page. For an image, write src with the image file name.",
                "Take file names and page names from the draft/page resources given in the question.",
            ),
            "Start with document structure": (
                "<html>\n<head>\n<title>Title from the draft</title>\n</head>\n<body>\n...\n</body>\n</html>",
                "The page title belongs in the draft browser/title area; visible page content belongs inside body.",
            ),
            "Map each draft item to a tag": (
                "<h1>Main heading</h1>\n<img src=\"given-image.jpg\" alt=\"description\">\n<p>Paragraph text</p>\n<a href=\"second-page.html\">Link text</a>",
                "Read the draft page from top to bottom and convert each visible item into the matching HTML tag.",
            ),
            "Use working attributes": (
                "Use src for the image file and href for the linked page, copying the file/page names exactly.",
                "The draft/resources usually give the image name and link target; those are the attribute values.",
            ),
            "Create the World class": (
                "Create a World subclass named exactly as requested, e.g. Advert, and set the 9 x 9 grid background image.",
                "Part (a) gives the world class name and background image.",
            ),
            "Create and image the Actor": (
                "Create the named Actor subclass and assign the requested image file.",
                "Part (b) normally gives the actor name and image file.",
            ),
            "Populate in the constructor": (
                "In the World constructor, add the required objects, e.g. addObject(new Sun(), 2, 4); and addObject(new Sun(), 6, 4);",
                "Use the number of objects stated in the populate instruction.",
            ),
            "Add random movement": (
                "In the Actor act method, write movement and random turning code, e.g. move(2); if (Greenfoot.getRandomNumber(100) < 10) { turn(Greenfoot.getRandomNumber(91) - 45); }",
                "This comes from the wording 'turn and move randomly'.",
            ),
            "Save with the final name": (
                "Save the scenario using the exact final name requested, such as FinalWJECSki7 or finalAdvert.",
                "The final subpart gives the save name; copy it exactly.",
            ),
            "Populate before coding": (
                "Add the player and all collectible/hazard objects so they are present when the world opens.",
                "Part (a) lists the objects and quantities required in the existing Greenfoot world.",
            ),
            "Separate random and player movement": (
                "Use random movement in non-player classes; use Greenfoot.isKeyDown(\"left\"), \"right\", \"up\" and \"down\" in the player class.",
                "Parts (b) and (c) split random object movement from arrow-key player movement.",
            ),
            "Handle collisions": (
                "Actor item = getOneIntersectingObject(Item.class); if (item != null) { getWorld().removeObject(item); }",
                "Use the subpart that says the player collects/eats/removes an object on collision.",
            ),
            "Add sound and counter": (
                "Play the named sound on collision and increment/update the counter when the object is collected.",
                "Later subparts usually mention sound and counter as separate marks.",
            ),
            "Save exactly as requested": (
                "Save the completed world with the exact final name in the question.",
                "The last subpart gives the required final world name.",
            ),
        }
        return details.get(title, ("Write the mark-scheme point as a short, direct answer.", "Use the command word and the named item in the question."))

    def create_demo_users(self):
        User = get_user_model()
        demo_users = [
            ("student", "chinchilla", "Sam", "Student", UserProfile.ROLE_STUDENT),
            ("teacher", "chinchilla", "Tara", "Teacher", UserProfile.ROLE_TEACHER),
            ("admin", "chinchilla", "Alex", "Admin", UserProfile.ROLE_ADMIN),
        ]
        created_users = {}
        for username, password, first_name, last_name, role in demo_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": f"{username}@example.com",
                    "is_staff": role == UserProfile.ROLE_ADMIN,
                },
            )
            user.set_password(password)
            user.is_staff = role == UserProfile.ROLE_ADMIN
            user.is_superuser = role == UserProfile.ROLE_ADMIN
            user.save()
            user.profile.role = role
            user.profile.save(update_fields=["role", "updated_at"])
            created_users[role] = user

        TeacherStudentAssignment.objects.get_or_create(
            teacher=created_users[UserProfile.ROLE_TEACHER],
            student=created_users[UserProfile.ROLE_STUDENT],
        )
