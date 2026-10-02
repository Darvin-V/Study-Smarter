"""
Study Smarter - Test Suite for Case-Based Question Service & Rendering
Validates:
1. Detecting case studies and extracting sub-questions with paragraphs attached.
2. Rendering the paragraph for each sub-question under a case study (e.g. 5 sub-questions).
3. Switching to a new paragraph when a new case-based section begins.
4. Graceful handling of regular non-case questions.
5. Splitting and rendering HTML cards accurately.
"""

import unittest
from src.services.case_study_service import CaseStudyService


class TestCaseStudyService(unittest.TestCase):

    def setUp(self):
        self.sample_case_text = """
(XVI) Read the passage given below and answer the following questions: 
Polysaccharides may be very large molecules. Starch, glycogen, cellulose, and chitin are examples of polysaccharides.
Starch is the stored form of sugars in plants and is made up of amylose and amylopectin.
Glycogen is the storage form of glucose in humans and other vertebrates, stored in liver and muscles.
Cellulose is one of the most abundant natural biopolymers in plant cell walls.

Based on the above answer the following:
1. In animals, Glycogen is stored in:
A. Liver
B. Spleen
C. Muscle
D. Both A and C

2. Amylose is:
A. Straight chain polymer of glucose
B. Branched chain polymer of fructose
C. Protein molecule
D. Lipid

3. Which biopolymer breaks down to release glucose when levels drop:
A. Glycogen
B. Cellulose
C. Chitin
D. Starch

4. The linkages which join monosaccharides to form polysaccharides:
A. Peptide linkage
B. Glycosidic linkage
C. Phosphodiester linkage
D. Hydrogen bond

5. Cellulose on complete hydrolysis yields:
A. Amylose
B. Amylopectin
C. Glucose
D. Fructose

CASE STUDY 2:
The Indian coast guard, while patrolling, saw a suspicious boat moving along a planar surface.
At an instant of time, coordinates of helicopter and boat are (1, 3, 5) and (2, 5, 3) respectively.

Based on the above information, answer the following:
1. What is the distance between helicopter and boat?
A. 3m
B. 5m
C. 6m
D. 4m

2. What is the equation of the plane?
A. x + 2y + 2z = 6
B. -x + 2y - 2z = 6
C. x - 2y + 2z = 6
D. 2x - y + z = 3
"""

    def test_parse_mcqs_with_cases_two_distinct_passages(self):
        """Tests that 5 questions under Passage 1 have Passage 1, and 2 questions under Case 2 have Case 2."""
        questions = CaseStudyService.parse_mcqs_with_cases(self.sample_case_text)
        self.assertEqual(len(questions), 7)

        # Check the first 5 questions (belonging to Polysaccharides passage)
        poly_passage = "Polysaccharides may be very large molecules"
        for i in range(5):
            q = questions[i]
            self.assertTrue(q.get("is_case_based"))
            self.assertIn(poly_passage, q["passage_text"])
            self.assertIn("[Case / Passage Context]", q["question"])
            self.assertIn(poly_passage, q["question"])

        # Specific sub-questions under Polysaccharide passage
        self.assertIn("In animals, Glycogen is stored in:", questions[0]["raw_question"])
        self.assertIn("Amylose is:", questions[1]["raw_question"])
        self.assertIn("Which biopolymer breaks down", questions[2]["raw_question"])
        self.assertIn("linkages which join monosaccharides", questions[3]["raw_question"])
        self.assertIn("Cellulose on complete hydrolysis yields:", questions[4]["raw_question"])

        # Check next 2 questions (belonging to Coast Guard case study)
        coast_passage = "The Indian coast guard, while patrolling"
        for i in range(5, 7):
            q = questions[i]
            self.assertTrue(q.get("is_case_based"))
            self.assertIn(coast_passage, q["passage_text"])
            self.assertNotIn(poly_passage, q["passage_text"])
            self.assertIn("[Case / Passage Context]", q["question"])

        self.assertIn("distance between helicopter and boat", questions[5]["raw_question"])
        self.assertIn("equation of the plane", questions[6]["raw_question"])

    def test_split_passage_and_question(self):
        """Tests splitting formatted question into passage and sub-question."""
        passage = "Carbon forms four covalent bonds due to its tetravalency."
        sub_q = "What is the hybridisation of carbon in methane?"
        formatted = CaseStudyService.format_case_question(passage, sub_q)

        p_out, q_out = CaseStudyService.split_passage_and_question(formatted)
        self.assertEqual(p_out, passage)
        self.assertEqual(q_out, sub_q)

        # Non-case question returns None for passage
        plain = "Which gas is evolved when zinc reacts with dilute sulfuric acid?"
        p_plain, q_plain = CaseStudyService.split_passage_and_question(plain)
        self.assertIsNone(p_plain)
        self.assertEqual(q_plain, plain)

    def test_render_question_card_html_case_vs_standard(self):
        """Tests HTML generation for both case-based and standard questions."""
        passage = "Enzymes are biological catalysts that speed up biochemical reactions."
        sub_q = "Which enzyme catalyzes the hydrolysis of starch into maltose?"
        formatted = CaseStudyService.format_case_question(passage, sub_q)

        html_case = CaseStudyService.render_question_card_html(formatted, question_num=1, topic_line="Biology · Enzymes")
        self.assertIn("📖", html_case)
        self.assertIn("Case / Context Passage", html_case)
        self.assertIn("Enzymes are biological catalysts", html_case)
        self.assertIn("Which enzyme catalyzes the hydrolysis", html_case)
        self.assertIn("Question 1", html_case)

        # Standard question
        plain = "What is the atomic number of Gold?"
        html_plain = CaseStudyService.render_question_card_html(plain, question_num=2, topic_line="Chemistry · Elements")
        self.assertNotIn("Case / Context Passage", html_plain)
        self.assertIn("What is the atomic number of Gold?", html_plain)
        self.assertIn("Question 2", html_plain)


if __name__ == "__main__":
    unittest.main()
