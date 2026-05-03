# Source Papers

Current authoritative Unit 2 papers and mark schemes supplied for analysis:

- `/Users/thomas/Desktop/S24-3500U20-1.pdf`
- `/Users/thomas/Desktop/S24-3500U20-1-ms.pdf`
- `/Users/thomas/Desktop/s23-3500u20-1.pdf`
- `/Users/thomas/Desktop/s23-3500u20-1-ms.pdf`
- `/Users/thomas/Desktop/z22-3500-02.pdf`
- `/Users/thomas/Desktop/s22-3500U20-1-ms.pdf`
- `/Users/thomas/Desktop/s19-3500-02.pdf`
- `/Users/thomas/Desktop/s19-3500u20-1 wjec gcse comp sci. - unit 2 ms s-ms.pdf`

Extraction notes:

- `pypdf` is now installed and `tools/extract_pdf_patterns.py` can scan the supplied PDFs for recurring WJEC Unit 2 terms.
- The extracted papers/mark schemes show the same recurring practical patterns:
  - early HTML questions asking for tag effects and HTML needed to match a draft web page;
  - a Greenfoot "create a new scenario" task with a new World class, Actor subclass, image, population, random movement, and final save name;
  - a Greenfoot "identify" task around superclass/class/object/constructor/act method;
  - a Greenfoot "complete an existing world" task with pre-population, random object movement, arrow-key player movement, collision removal, sound, counter, and final save name.

Implementation notes:

- Seed data now focuses on those HTML and Greenfoot patterns rather than generic GCSE computing questions.
- `python manage.py import_past_papers --replace` imports the structured question bank for the supplied 2019, 2022, 2023 and 2024 paper/mark-scheme set.
- Generated questions should use these patterns as templates and vary the scenario nouns/images/object names, not invent unrelated Unit 2 theory questions.
- A production importer should still extract full paper text, identify question references and mark points, and queue teacher review before publishing.
