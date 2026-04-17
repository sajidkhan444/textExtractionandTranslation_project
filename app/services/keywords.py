# app/services/keywords.py

import torch
from app.utils.chunking import chunk_text_multilang
from app.core.model_registry import models


def _extract_keywords_batch(prompts):
    """Extract keywords from a batch of prompts using Qwen"""
    tokenizer = models.qwen_tokenizer
    model = models.qwen_model

    inputs = tokenizer(
        prompts,
        padding=True,
        truncation=True,
        max_length=1024,
        return_tensors="pt"
    ).to(model.device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            do_sample=False,
            temperature=0.1,
            repetition_penalty=1.1,
        )

    decoded = tokenizer.batch_decode(outputs, skip_special_tokens=True)

    cleaned_outputs = []

    for text in decoded:
        if "assistant" in text:
            text = text.split("assistant")[-1].strip()

        text = text.split("\n")[0].strip()

        keywords = [k.strip() for k in text.split("|") if k.strip()]

        seen = set()
        unique = []

        for k in keywords:
            low = k.lower()
            if low not in seen:
                seen.add(low)
                unique.append(k)

        cleaned_outputs.append(unique)

    return cleaned_outputs


def extract_keywords_batch_hybrid(normalized_texts, use_llm=True):
    """
    Extract keywords from a batch of normalized texts.
    Uses Qwen LLM first, falls back to KeyBERT if needed.
    """
    batch_results = []

    for text in normalized_texts:
        chunks = chunk_text_multilang(text, max_tokens=350)
        chunk_prompts = []

        for chunk in chunks:
            # FIXED: Properly define messages with system prompt
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a keyword extraction system. Extract keywords ONLY from the text provided.\n\n"
                        "========== COMPLETE DOMAIN & PROFESSION REFERENCE ==========\n\n"
                        "TECHNOLOGY & IT:\n"
                        "- Programming: Python, JAVA, C++, JavaScript, Go, Rust, SQL, HTML, CSS, PHP, Ruby, Swift, Kotlin\n"
                        "- Frameworks: FastAPI, React, Angular, Vue, Django, Spring Boot, Flask, Laravel, Rails, TensorFlow, PyTorch\n"
                        "- Cloud/DevOps: AWS, Azure, GCP, Docker, Kubernetes, Jenkins, Terraform, Ansible, CI/CD, Linux\n"
                        "- Data/AI: Machine Learning, Deep Learning, NLP, Computer Vision, LLM, RAG, Vector Database, Pandas, NumPy\n"
                        "- Roles: software developer, data scientist, DevOps engineer, cloud architect, ML engineer, frontend developer, backend developer, fullstack developer, QA engineer, security analyst, database administrator, system administrator\n\n"
                        
                        "CONSTRUCTION & TRADES:\n"
                        "- Roles: plumber, electrician, carpenter, welder, mason, painter, roofer, HVAC technician, heavy equipment operator, construction manager, site supervisor, civil engineer, architect, surveyor\n"
                        "- Skills: pipe fitting, wiring, circuit installation, framing, drywall, flooring, tiling, concrete pouring, scaffolding, excavation, blueprint reading, load calculation\n"
                        "- Equipment: multimeter, pipe wrench, soldering iron, welding torch, drill, saw, level, laser measurer, excavator, crane, bulldozer\n\n"
                        
                        "MEDICAL & HEALTHCARE:\n"
                        "- Roles: doctor, nurse, surgeon, physician, pharmacist, radiologist, lab technician, paramedic, physical therapist, dentist, veterinarian, cardiologist, neurologist, dermatologist, anesthesiologist\n"
                        "- Tests/Procedures: blood pressure checking, sugar test, cholesterol test, MRI, CT scan, X-ray, ultrasound, ECG, endoscopy, biopsy, vaccination, surgery, physical examination\n"
                        "- Equipment: stethoscope, thermometer, sphygmomanometer, glucometer, defibrillator, ventilator, infusion pump, microscope, centrifuge, ECG machine, X-ray machine\n"
                        "- Specialties: cardiology, neurology, orthopedics, pediatrics, gynecology, urology, ophthalmology, psychiatry, radiology, pathology, emergency medicine, family medicine\n\n"
                        
                        "AUTOMOTIVE & MECHANICAL:\n"
                        "- Roles: mechanic, auto technician, diesel mechanic, aircraft mechanic, marine mechanic, welder, machinist, tool maker, maintenance engineer\n"
                        "- Skills: engine repair, brake service, transmission repair, oil change, tire rotation, alignment, battery replacement, diagnostics, welding, fabrication, CNC operation\n"
                        "- Equipment: OBD scanner, torque wrench, jack stand, lift, multimeter, soldering gun, lathe, milling machine, plasma cutter\n\n"
                        
                        "HOSPITALITY & FOOD SERVICE:\n"
                        "- Roles: chef, cook, baker, sous chef, pastry chef, line cook, dishwasher, server, bartender, barista, host, restaurant manager, catering manager, food service director\n"
                        "- Skills: food preparation, plating, knife skills, sauce making, baking, grilling, sautéing, food safety, inventory management, menu planning, customer service\n"
                        "- Equipment: oven, stove, grill, fryer, mixer, food processor, refrigerator, freezer, dishwasher, espresso machine\n\n"
                        
                        "RETAIL & SALES:\n"
                        "- Roles: cashier, sales associate, store manager, merchandiser, visual merchandiser, buyer, stock clerk, customer service representative, retail assistant\n"
                        "- Skills: point of sale operation, inventory management, stocking, pricing, display setup, customer handling, upselling, cross-selling, returns processing\n\n"
                        
                        "EDUCATION & ACADEMIA:\n"
                        "- Roles: teacher, professor, instructor, lecturer, tutor, teaching assistant, principal, dean, counselor, librarian, researcher, academic advisor\n"
                        "- Subjects: mathematics, science, English, history, geography, physics, chemistry, biology, economics, psychology, sociology, computer science, art, music, physical education\n"
                        "- Skills: lesson planning, curriculum development, grading, student assessment, classroom management, lecture delivery, research, paper writing, thesis supervision\n\n"
                        
                        "BUSINESS & FINANCE:\n"
                        "- Roles: accountant, financial analyst, investment banker, auditor, tax consultant, payroll specialist, bookkeeper, CFO, controller, actuary, economist\n"
                        "- Skills: financial reporting, budgeting, forecasting, auditing, tax preparation, payroll processing, bookkeeping, risk assessment, portfolio management, stock trading\n"
                        "- Tools: QuickBooks, SAP, Oracle, Excel, Bloomberg Terminal, Salesforce, Tableau, Power BI\n\n"
                        
                        "LEGAL & COMPLIANCE:\n"
                        "- Roles: lawyer, attorney, paralegal, legal assistant, judge, prosecutor, defense attorney, corporate counsel, compliance officer, legal secretary\n"
                        "- Skills: contract drafting, litigation, legal research, case management, client counseling, document review, deposition, arbitration, mediation, regulatory compliance\n\n"
                        
                        "CREATIVE & DESIGN:\n"
                        "- Roles: graphic designer, UI designer, UX designer, web designer, art director, illustrator, animator, video editor, photographer, content creator, copywriter, art therapist\n"
                        "- Skills: Photoshop, Illustrator, Figma, Sketch, InDesign, Premiere Pro, After Effects, Blender, Maya, 3D modeling, typography, color theory, branding, layout design\n\n"
                        
                        "MANUFACTURING & INDUSTRIAL:\n"
                        "- Roles: production operator, assembly line worker, quality control inspector, warehouse worker, forklift operator, logistics coordinator, supply chain manager, plant manager\n"
                        "- Skills: assembly, packaging, quality testing, inventory counting, forklift operation, shipping, receiving, palletizing, barcode scanning, lean manufacturing, Six Sigma\n"
                        "- Equipment: conveyor belt, forklift, pallet jack, barcode scanner, scale, caliper, micrometer, CMM machine, robotic arm\n\n"
                        
                        "AGRICULTURE & FARMING:\n"
                        "- Roles: farmer, rancher, agricultural worker, farm manager, crop specialist, livestock handler, veterinarian, agronomist, horticulturist, tractor operator\n"
                        "- Skills: planting, harvesting, irrigation, fertilization, pest control, animal feeding, breeding, milking, shearing, soil testing, crop rotation\n"
                        "- Equipment: tractor, plow, harvester, irrigation system, sprayer, baler, milking machine, combine, cultivator, seeder\n\n"
                        
                        "TRANSPORTATION & LOGISTICS:\n"
                        "- Roles: truck driver, delivery driver, bus driver, pilot, flight attendant, train conductor, ship captain, logistics coordinator, dispatcher, warehouse manager\n"
                        "- Skills: route planning, load securing, fuel management, vehicle inspection, cargo handling, documentation, tracking, dispatching\n\n"
                        
                        "ENERGY & UTILITIES:\n"
                        "- Roles: electrician, lineman, power plant operator, solar installer, wind turbine technician, oil rig worker, pipeline operator, energy analyst, utility worker\n"
                        "- Skills: line repair, meter reading, solar panel installation, turbine maintenance, drilling, pipeline inspection, grid monitoring, load balancing\n\n"
                        
                        "MILITARY & SECURITY:\n"
                        "- Roles: security guard, police officer, firefighter, soldier, private investigator, bodyguard, security manager, surveillance operator, cybersecurity analyst\n"
                        "- Skills: patrol, access control, CCTV monitoring, alarm response, threat assessment, incident reporting, crowd control, firearms handling, self-defense\n\n"
                        
                        "========== EXTRACTION RULES ==========\n\n"
                        "ALLOWED KEYWORD TYPES (ONLY if explicitly mentioned):\n"
                        "- Any profession/role from above domains or similar\n"
                        "- Any skill, tool, equipment, or technology\n"
                        "- Any medical test, procedure, or specialty\n"
                        "- Any programming language, framework, or platform\n"
                        "- Any trade or hands-on skill\n\n"
                        
                        "STRICT PROHIBITIONS:\n"
                        "❌ Do NOT invent keywords not explicitly in the text\n"
                        "❌ Do NOT generalize (e.g., 'JAVA' → NOT 'programming')\n"
                        "❌ Do NOT output names of people or locations\n"
                        "❌ Do NOT output verbs or actions (keep noun phrases)\n"
                        "❌ Do NOT output categories, headings, or explanations\n"
                        "❌ Do NOT output filler words (using, with, have, like, know, work)\n"
                        "❌ If NO allowed keyword exists, output: NONE\n\n"
                        
                        "OUTPUT FORMAT:\n"
                        "- Pipe-separated list: keyword1 | keyword2 | keyword3\n"
                        "- Preserve original casing\n"
                        "- ONE line only\n"
                        "- If no keywords, output: NONE\n\n"
                        
                        "========== EXAMPLES ==========\n\n"
                        "Example 1 (Multi-domain):\n"
                        "Text: 'I am a software developer using JAVA and FastAPI. Also a plumber with pipe fitting experience.'\n"
                        "Output: software developer | JAVA | FastAPI | plumber | pipe fitting\n\n"
                        
                        "Example 2 (Medical only):\n"
                        "Text: 'I check blood pressure, do sugar test, and use stethoscope as a nurse'\n"
                        "Output: blood pressure | sugar test | stethoscope | nurse\n\n"
                        
                        "Example 3 (No valid keywords):\n"
                        "Text: 'My name is John and I like playing cricket'\n"
                        "Output: NONE\n\n"
                        
                        "Example 4 (Construction):\n"
                        "Text: 'I work as an electrician, do wiring, and use multimeter'\n"
                        "Output: electrician | wiring | multimeter\n"
                    )
                },
                {"role": "user", "content": chunk}
            ]

            # FIXED: Use the messages variable correctly
            prompt = models.qwen_tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )

            chunk_prompts.append(prompt)

        if use_llm:
            try:
                llm_chunk_results = _extract_keywords_batch(chunk_prompts)

                merged = []
                seen = set()

                for kws in llm_chunk_results:
                    for k in kws:
                        low = k.lower()
                        if low not in seen:
                            seen.add(low)
                            merged.append(k)

                if len(merged) >= 3:
                    batch_results.append(merged)
                    continue

            except Exception as e:
                print("LLM chunk failed, fallback:", e)

        # Fallback to KeyBERT if LLM fails or returns insufficient keywords
        fallback = models.keybert_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words="english",
            top_n=10,
            diversity=0.5
        )

        batch_results.append([kw for kw, _ in fallback])

    return batch_results